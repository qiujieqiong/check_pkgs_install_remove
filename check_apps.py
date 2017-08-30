#!/usr/bin/env python3

import pyautogui
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 1
import dbus
from subprocess import getoutput, getstatusoutput
from time import sleep
import unittest
import threading
import os, sys
import gi
gi.require_version('Wnck', '3.0')
from gi.repository import Wnck
import pandas as pd
import pexpect
import time


secs_between_keys = 0.5

JSON_PATH = '/var/lib/lastore/applications.json'
list_pkgs_cmd = 'lastore-tools test -j search'
install_cmd = 'lastore-tools test -j install '
desktop_cmd = 'lastore-tools querydesktop '
remove_cmd = 'lastore-tools test -j remove '
config_cmd = 'sudo dpkg --configure -a'
fix_broken_cmd = 'sudo apt-get -fy install'


def get_default_pkgs():
	DIRNAME = '/usr/share/applications'
	desktopfiles = [file for file in os.listdir(DIRNAME) if
					file.endswith('.desktop') and 'cxassoc-cxoffice' not in file]
	pkgs_name = [getoutput('dpkg -S ' + desktopfile) for desktopfile in desktopfiles]
	return [pkg_name[:pkg_name.find(':')] for pkg_name in pkgs_name]


default_apps = get_default_pkgs()
need_passwd_apps = ['cpu-g', 'cinelerra', 'gparted', 'mintdrivers', 'synaptic', 'gufw', 'vmware-workstation-install', 'unetbootin', 'tickeys', 'myeclipse']


def getAllWindowsPid():
	screen = Wnck.Screen.get_default()
	screen.force_update()
	winspid = []
	screen = Wnck.Screen.get_default()
	screen.force_update()
	for win in screen.get_windows():
		winspid.append(win.get_pid())
	screen = None
	Wnck.shutdown()
	return winspid

def getpids():
	pscmd = 'ps -eo pid --no-headers'
	pids = getoutput(pscmd).split('\n')
	return pids

def getapps():
	#apps = [a['id'] for a in json.loads(open(JSON_PATH, 'r').read()).values()]
	o = getoutput(list_pkgs_cmd)
	pkgsobj = [Pkgs(pkg) for pkg in o.split('\n')]
	#pkgs = ['libflashplugin-pepper']
	#pkgsobj = [Pkgs(pkg) for pkg in pkgs]
	return pkgsobj


def get_desktop_name(pkgname):
	'''
	dbusDir = 'com.deepin.lastore'
	dbusObj = '/com/deepin/lastore'
	ifc = 'com.deepin.lastore.Manager'
	system_bus = dbus.SystemBus()
	system_obj = system_bus.get_object(dbusDir, dbusObj)
	system_if = dbus.Interface(system_obj, dbus_interface=ifc)
	desktop_path = system_if.PackageDesktopPath(pkgname)
	if desktop_path == '':
		return
	'''
	desktop_path = getoutput(desktop_cmd + pkgname)
	if desktop_path == '':
		return
	return desktop_path


def getTrayIcons():
	dbusDir = 'com.deepin.dde.TrayManager'
	dbusObj = '/com/deepin/dde/TrayManager'
	ifc = 'com.deepin.dde.TrayManager'
	trayicons = 'TrayIcons'
	session_bus = dbus.SessionBus()
	session_obj = session_bus.get_object(dbusDir, dbusObj)
	property_obj = dbus.Interface(session_obj, dbus_interface=dbus.PROPERTIES_IFACE)
	dbus_array = property_obj.Get(ifc, trayicons)
	icons = [str(icon) for icon in dbus_array]
	return icons

def get_desktop_exec(pkgname):
	desktop_path = get_desktop_name(pkgname)
	if desktop_path is None:
		return
	else:
		o = getoutput('cat ' + desktop_path.replace(' ','\ ') + '|grep Exec= |head -1')
		start = o.find('=') + 1
		end = o.rfind('%')-1 if o.find('%') != -1 else len(o)
		return o[start:end]


def fix_install_failed():
	getstatusoutput(config_cmd)
	getstatusoutput(fix_broken_cmd)

def install_app(app):
	fix_install_failed()
	s, o = getstatusoutput(install_cmd + app)
	return s, o


def remove_app(app):
	getoutput(config_cmd)
	s, o = getstatusoutput(remove_cmd + app)
	return s, o


def run_app(app):
	t = threading.Thread(target=lambda: getoutput(get_desktop_exec(app.pkg_name)))
	t.setDaemon(True)
	t.start()



def app_isInstalled(app):
	s, o = getstatusoutput('dpkg -l ' + app)
	if s == 0:
		return True
	else:
		return False


def convertToHtml(result, title):
	d = {}
	index = 0
	for t in title:
		d[t] = result[index]
		index = index + 1
	df = pd.DataFrame(d)
	df = df[title]
	h = df.to_html(index=False)
	return h


class Window:
	def __init__(self, pid):
		self.pid = pid


	def close(self):
		print('close window: %s' % self.pid)
		screen = Wnck.Screen.get_default()
		screen.force_update()
		for win in screen.get_windows():
			if self.pid == win.get_pid():
				win.close(1)
		screen = None
		Wnck.shutdown()



class Pkgs:
	def __init__(self, pkgname):
		self.pkg_name = pkgname
		self.installed_status = ''
		self.opened_status = ''
		self.removed_status = ''
		self.desktop_path = ''
		self.exec_str = ''


	def killps(self,pid):
		print('kill %s' % pid)
		getoutput('sudo kill -9 ' + pid)


class Apps(unittest.TestCase):
	@classmethod
	def setUpClass(cls):
		cls.starttime = time.ctime()
		cls.existed_services = []
		cls.install_passed = []
		cls.install_failed = []
		cls.opened_passed = []
		cls.opened_failed = []
		cls.remove_passed = []
		cls.remove_failed = []
		cls.trayicon = []

		cls.apps = getapps()
		names = [app.pkg_name for app in cls.apps]
		print(names)
		cls.defaultWindows = getAllWindowsPid()
		with open('pkgs.info', 'w') as f:
			f.write('pkgs install/open/remove info:\n\n')
		f.close()
	@classmethod
	def tearDownClass(cls):
		num = [i+1 for i in range(len(cls.apps))]
		names = [app.pkg_name for app in cls.apps]
		execstr = [app.exec_str for app in cls.apps]
		desktoppath = [app.desktop_path for app in cls.apps]
		install_status = [app.installed_status for app in cls.apps]
		open_status = [app.opened_status for app in cls.apps]
		remove_status = [app.removed_status for app in cls.apps]
		result = [num, names, execstr, desktoppath, install_status, open_status, remove_status]
		title = ['number', 'name', 'exec_cmd', 'desktop_file', 'install_status', 'open_status', 'remove_status']
		with open('result.html', 'w') as f:
			f.write(convertToHtml(result, title))
		f.close()
		with open('pkgs.info', 'a') as f:
			f.write('pkgs in trayicon\n\n')
			for tray in cls.trayicon:
				f.write(tray+'\n')
			nodesktopfile = [app.pkg_name for app in cls.apps if app.desktop_path is None and app.installed_status != 'failed']
			f.write('pkgs no desktopfile:\n\n')
			for nodesktopfileapp in nodesktopfile:
				f.write(nodesktopfileapp+'\n')
			f.write('pkgs install failed:\n\n')
			for install_app in cls.install_failed:
				f.write(install_app+'\n')
			f.write('pkgs open failed:\n\n')
			for open_app in cls.opened_failed:
				f.write(open_app+'\n')
			f.write('pkgs remove failed:\n\n')
			for remove_app in cls.remove_failed:
				f.write(remove_app+'\n')
			f.write(cls.starttime+'\n')
			f.write(time.ctime()+'\n')
		f.close()
		cls.newWindows = getAllWindowsPid()
		if len(cls.newWindows) > len(cls.defaultWindows):
			for win in cls.newWindows[len(cls.defaultWindows):]:
				Window(win).close()

	def test_update(self):
		s, o = getstatusoutput('lastore-tools test -j update')

	def test_apps(self):
		with open('pkgs.info', 'a') as f:
			for app in self.apps:
				if app.pkg_name == 'draftsight':
					continue
				# install
				if app.pkg_name in default_apps:
					app.installed_status = 'existed'
				defaultWindows = getAllWindowsPid()
				defaultpids = getpids()
				defaulttrayicons = getTrayIcons()
				if app.pkg_name not in default_apps:
					s, o = install_app(app.pkg_name)
					if s == 0:
						app.installed_status = 'passed'
						self.install_passed.append(app.pkg_name)
						print('install %s passed\n' % app.pkg_name)
					elif s != 0 and app_isInstalled(app.pkg_name):
						app.installed_status = 'existed'
						self.existed_services.append(app.pkg_name)
					else:
						app.installed_status = 'failed'
						self.install_failed.append(app.pkg_name)
						f.write('[%s] install failed:\n %s\n\n' % (app.pkg_name, o))
						print('install %s failed\n' % app.pkg_name)
				app.desktop_path = get_desktop_name(app.pkg_name)
				app.exec_str = get_desktop_exec(app.pkg_name)
				print('app [%s] run cmd [%s] ' % (app.desktop_path,app.exec_str))

				# run app
				if app.desktop_path is not None:
					run_app(app)
					if app.pkg_name in need_passwd_apps:
						sleep(2)
						pyautogui.typewrite(sys.argv[1], interval=1)
						pyautogui.press('enter')
						sleep(1)
					wait = 30
					while wait != 0:
						sleep(1)
						wait = wait - 1
						newWindows = getAllWindowsPid()
						if len(newWindows) > len(defaultWindows):
							app.opened_status = 'passed'
							print(defaultWindows)
							print(newWindows)
							self.opened_passed.append(app.pkg_name)
							print('opened %s passed\n' % app.pkg_name)
							WindowsPid = list(set(newWindows).symmetric_difference(set(defaultWindows)))
							print(WindowsPid)
							for winpid in WindowsPid:
								Window(winpid).close()
							break
					else:
						newtrayicons = getTrayIcons()
						if len(newtrayicons) > len(defaulttrayicons):
							trayicons = list(set(newtrayicons).symmetric_difference(set(defaulttrayicons)))
							print(trayicons)
							self.trayicon.append(app.pkg_name)
							print('opened %s passed\n' % app.pkg_name)
							app.opened_status = 'passed'
							self.opened_passed.append(app.pkg_name)
						else:
							app.opened_status = 'failed'
							print(defaultWindows)
							print(getAllWindowsPid())
							self.opened_failed.append(app.pkg_name)
							f.write('[%s] run [%s] open failed \n' % (app.pkg_name,get_desktop_exec(app.pkg_name)))
							print('opened %s failed\n' % app.pkg_name)
				sleep(2)
				externalpids = getpids()
				if len(externalpids) > len(defaultpids):
					apppids = list(set(externalpids).symmetric_difference(set(defaultpids)))
					for pid in apppids:
						app.killps(pid)
				# remove app
				no_need_remove_apps = list(set(default_apps).union(self.existed_services))
				if app.pkg_name not in no_need_remove_apps:
					s, o = remove_app(app.pkg_name)

					if s == 0:
						app.removed_status = 'passed'
						self.remove_passed.append(app.pkg_name)
						print('remove %s passed\n' % app.pkg_name)
					else:
						f.write('[%s] remove failed: \n %s\n\n' % (app.pkg_name, o))
						app.removed_status = 'failed'
						self.remove_failed.append(app.pkg_name)
						print('remove %s failed\n' % app.pkg_name)
				else:
					app.removed_status = 'default app, do not remove'


		f.close()




apps = Apps()


def suite():
	suite = unittest.TestSuite()
	suite.addTest(Apps('test_update'))
	suite.addTest(Apps('test_apps'))
	return suite


alltests = unittest.TestSuite(suite())

if __name__ == '__main__':

	if len(sys.argv) < 2:
		print('please input your system password after check_apps.py\n')
		print('python3 check_apps.py password\n')
		sys.exit()

	with open('test.result', 'w') as logf:
		unittest.TextTestRunner(stream=logf, verbosity=2).run(alltests)
	logf.close()

# unittest.TextTestRunner(verbosity=2).run(alltests)
