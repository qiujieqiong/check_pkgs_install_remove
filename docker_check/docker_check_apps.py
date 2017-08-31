#!/usr/bin/env python3


import dbus
from subprocess import getoutput, getstatusoutput
from time import sleep
import unittest
import threading
import os, sys
import time
import apt


JSON_PATH = '/var/lib/lastore/applications.json'
list_pkgs_cmd = 'lastore-tools test -j search'
install_cmd = 'lastore-tools test -j install '
desktop_cmd = 'lastore-tools querydesktop '
remove_cmd = 'lastore-tools test -j remove '
config_cmd = 'sudo dpkg --configure -a'
fix_broken_cmd = 'sudo apt-get -fy install'

'''
def get_default_pkgs():
	DIRNAME = '/usr/share/applications'
	desktopfiles = [file for file in os.listdir(DIRNAME) if
					file.endswith('.desktop') and 'cxassoc-cxoffice' not in file]
	pkgs_name = [getoutput('dpkg -S ' + desktopfile) for desktopfile in desktopfiles]
	return [pkg_name[:pkg_name.find(':')] for pkg_name in pkgs_name]


default_apps = get_default_pkgs()
need_passwd_apps = ['cpu-g', 'cinelerra', 'gparted', 'mintdrivers', 'synaptic', 'gufw', 'vmware-workstation-install', 'unetbootin', 'tickeys', 'myeclipse']

'''


def getpids():
	pscmd = 'ps -eo pid --no-headers'
	pids = getoutput(pscmd).split('\n')
	return pids

def getapps():
	#apps = [a['id'] for a in json.loads(open(JSON_PATH, 'r').read()).values()]
	o = getoutput(list_pkgs_cmd)
	pkgsobj = [Pkgs(pkg) for pkg in o.split('\n')[:2]]
	#pkgs = ['libflashplugin-pepper']
	#pkgsobj = [Pkgs(pkg) for pkg in pkgs]
	return pkgsobj


def get_desktop_name(pkgname):

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
	'''
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


		cls.apps = getapps()
		names = [app.pkg_name for app in cls.apps]
		print(names)
		cls.pkgs_info = open('pkgs.info', 'w')
		cls.apt_cache = apt.cache.Cache()
		cls.apt_cache.update()



	@classmethod
	def tearDownClass(cls):
		num = [i + 1 for i in range(len(cls.apps))]
		names = [app.pkg_name for app in cls.apps]
		execstr = [app.exec_str for app in cls.apps]
		desktoppath = [app.desktop_path for app in cls.apps]
		install_status = [app.installed_status for app in cls.apps]
		remove_status = [app.removed_status for app in cls.apps]
		result = [num, names, execstr, desktoppath, install_status, remove_status]
		title = ['number', 'name', 'exec_cmd', 'desktop_file', 'install_status', 'remove_status']
		with open('result.html', 'w') as f:
			f.write(convertToHtml(result, title))
		f.close()



	def writeoneinfo(self, info):
		self.pkgs_info.write(info + '\n')
		#self.pkgs_info.close()


	def install(self, app):
		self.apt_cache.update()
		#if app.pkg_name == 'draftsight':
		#	return
		# install
		pkg = self.apt_cache[app.pkg_name]

		if pkg.is_installed:
			app.installed_status = 'existed'

		else:
			pkg.mark_install()
			try:
				self.apt_cache.commit()
			except Exception as e:
				app.installed_status = 'failed'
				self.install_failed.append(app.pkg_name)
				#self.writeinfo(app.pkg_name, status='install', err=str(e))
		app.desktop_path = get_desktop_name(app.pkg_name)

	def remove(self, app):
		self.apt_cache.open(None)
		pkg = self.apt_cache[app.pkg_name]
		self.apt_cache.update()
		pkg.mark_delete(True, purge=True)
		resolver = apt.cache.ProblemResolver(self.apt_cache)

		if pkg.is_installed is False:
			print(app.pkg_name + " not installed so not removed")
		else:
			for pkg in self.apt_cache.get_changes():
				if pkg.mark_delete:
					print(app.pkg_name + " is installed and will be removed")
					print(" %d package(s) will be removed" % self.apt_cache.delete_count)
					resolver.remove(pkg)
		try:
			self.apt_cache.commit()
		except Exception as e:
			app.removed_status = 'failed'
			self.remove_failed.append(app.pkg_name)
			#self.writeinfo(app.pkg_name, status='remove', err=str(e))

	def test_update(self):
		s, o = getstatusoutput('lastore-tools test -j update')

	def test_apps(self):
		for app in self.apps:
			self.install(app)
			self.remove(app)
		nodesktopfile = [app.pkg_name for app in self.apps if
						 app.desktop_path is None and app.installed_status != 'failed']
		self.writeoneinfo('pkgs no desktopfile')
		for nodesktopfileapp in nodesktopfile:
			self.writeoneinfo(nodesktopfileapp)
			self.writeoneinfo('pkgs install failed:')
		for install_app in self.install_failed:
			self.writeoneinfo(install_app)
			self.writeoneinfo('pkgs remove failed:')
		for remove_app in self.remove_failed:
			self.writeoneinfo(remove_app)
		self.writeoneinfo(self.starttime)
		self.writeoneinfo(time.ctime())

def suite():
	suite = unittest.TestSuite()
	suite.addTest(Apps('test_update'))
	suite.addTest(Apps('test_apps'))
	return suite


alltests = unittest.TestSuite(suite())

if __name__ == '__main__':
	with open('test.result', 'w') as logf:
		unittest.TextTestRunner(stream=logf, verbosity=2).run(alltests)
	logf.close()

# unittest.TextTestRunner(verbosity=2).run(alltests)
