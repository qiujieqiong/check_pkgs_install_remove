import os


def get_repo_review():
    base = os.environ['BASE']
    base_codename = os.environ['BASE_CODENAME']
    rpa = os.environ['RPA']
    rpa_codename = os.environ['RPA_CODENAME']
    upstream = os.environ['UPSTREAM']
    source_list_base = "deb %s %s main contrib non-free" % (base, base_codename)
    source_list_rpa = "deb %s %s main contrib non-free" % (rpa, rpa_codename)
    base_list_file = open('base.list', 'w')
    base_list_file.write(source_list_base)
    base_list_file.close()
    rpa_list_file = open('rpa.list', 'w')
    rpa_list_file.write(source_list_rpa)
    rpa_list_file.close()
    upstream_list_file = open('upstream.list', 'w')
    upstream_list_file.write(upstream)
    upstream_list_file.close()

if __name__ == '__main__':
    get_repo_review()
