import urllib2
import urllib

def test_common():
    urls = ["temp", "airflow", "fanspeed","power", "thermal", "hosts"]
    def get_url(url):
        req = urllib2.Request("http://10.239.52.36:8080/v1/common/%s" %url)
        response = urllib2.urlopen(req)
        ret = response.read()
        print "#"* 80
        print(ret)
    for url in urls:
        get_url(url)

#test_common()

def test_openstack_config():
    url = 'http://10.239.52.36:8080/v1/openstack/config'
    values = {"dispatch": "THERMAL",
              "migration": "OUTLETTEMP",
              "outlet_temp": 50}

    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    response = urllib2.urlopen(req)
    the_page = response.read()
    print(the_page)

test_openstack_config()
