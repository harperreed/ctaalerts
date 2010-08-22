import urllib  
import urllib2
from BeautifulSoup import BeautifulStoneSoup
import re


# ctaalerts.py
# CTAAlerts Api Consumer
# harper reed (harper@nata2.org)

# This class will consume and parse the Chicago Transit Authority alerts system. 

class CTAAlerts:

    api_version = '1.0'
    api_root = 'http://www.transitchicago.com/api/'+api_version+'/'

    def __init__(self):
        pass

    # http://love-python.blogspot.com/2008/07/strip-html-tags-using-python.html
    def remove_html_tags(self, data):
        p = re.compile(r'<.*?>')
        return p.sub('', data)

    def remove_extra_spaces(self,data):
        p = re.compile(r'\s+')
        return p.sub(' ', data)

    def make_request(self, endpoint, values):
        api_url = self.api_root + endpoint
        data = urllib.urlencode(values)
        url = api_url + "?"+data
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        content = response.read()
        return content

    def detailed_alerts(self, route_id='', station_id='', by_start_date='', recent_days='', active_only='', accessibility='', planned=''):
        alerts_xml = self.get_detailed_alerts_xml(route_id, station_id, by_start_date, recent_days, active_only, accessibility, planned)
        detailed_alerts= self.parse_detailed_alerts_xml(alerts_xml)
        return detailed_alerts

    def get_detailed_alerts_xml(self, route_id='', station_id='', by_start_date='', recent_days='', active_only='', accessibility='', planned=''):
        endpoint = 'alerts.aspx'
        values = {
                  'routeid' : route_id,
                  'stationid' : station_id,
                  'recentdays' : recent_days,
                  'activeonly' : active_only,
                  'accessibility' : accessibility,
                  'planned' : planned
                  }
        content = self.make_request(endpoint, values)
        return content

    def parse_detailed_alerts_xml(self, alerts_xml):
        parsed = BeautifulStoneSoup(alerts_xml)
        cta_alerts = parsed.ctaalerts
        detailed_alerts = {}
        try:
            detailed_alerts['errorcode'] = int(cta_alerts.errorcode.string)
            detailed_alerts['errormessage'] = cta_alerts.errormessage.string
        except:
            detailed_alerts['errorcode'] = 0
        detailed_alerts['timestamp'] = cta_alerts.timestamp.string

        if detailed_alerts['errorcode'] == 0:
            alerts = []
            alerts_x = parsed.findAll('alert')
            for a in alerts_x:
                alert = {}
                alert['alert_id'] = a.alertid.string
                alert['headline'] = a.headline.string
                alert['short_description'] = a.shortdescription.string
                alert['full_description'] = a.fulldescription.string
                alert['severity_score'] = a.severityscore.string
                alert['severity_color'] = a.severitycolor.string
                alert['severity_css'] = a.severitycss.string
                alert['impact'] = a.impact.string
                alert['event_start'] = a.eventstart.string
                alert['event_end'] = a.eventend.string
                alert['tbd'] = a.tbd.string
                alert['major_alert'] = a.majoralert.string
                alert['alert_url'] = a.alerturl.string

                impacted_service = []
                impacted_service_x = a.impactedservice.findAll('service')
                for s in impacted_service_x:
                    service = {}
                    service['service_type']= s.servicetype.string
                    service['service_type_description']= s.servicetypedescription.string
                    service['service_name']= s.servicename.string
                    service['service_id']= s.serviceid.string
                    service['service_backcolor']= s.servicebackcolor.string
                    service['service_textcolor']= s.servicetextcolor.string
                    service['service_url']= s.serviceurl.string
                    impacted_service.append(service)
                alert['impacted_service']=impacted_service

                alerts.append( alert)

            detailed_alerts['alerts'] = alerts
        return detailed_alerts

    def route_status(self, type='', route_id='', station_id=''):
        route_xml = self.get_route_status_xml(type, route_id, station_id)
        route_status = self.parse_route_status_xml(route_xml)
        return route_status

    def get_route_status_xml(self, type='', route_id='', station_id=''):
        endpoint = 'routes.aspx'
        values = {'type' : type,
                  'routeid' : route_id,
                  'stationid' : station_id }
        content = self.make_request(endpoint, values)
        return content

    def parse_route_status_xml(self, route_xml):
        parsed = BeautifulStoneSoup(route_xml)
        status = {} 
        cta_routes = parsed.ctaroutes
        try:
            status['errorcode'] = int(cta_routes.errorcode.string)
            status['errormessage'] = cta_routes.errormessage.string
        except:
            status['errorcode'] = 0
        status['timestamp'] = cta_routes.timestamp.string

        if (status['errorcode']==0):
            routes = []
            routes_x = parsed.findAll('routeinfo')
            for ri in routes_x:
                route_info = {}
                route_info['route'] = ri.route.string
                route_info['routecolorcode'] = ri.routecolorcode.string
                route_info['routeurl'] = ri.routeurl.string
                route_info['routestatus'] = ri.routestatus.string
                route_info['routestatuscolor'] = ri.routestatuscolor.string
                route_info['serviceid'] = ri.serviceid.string
                routes.append(route_info)
            status['route_info']=routes

        return status 

    # welcome to the sketchy part of our presentation. 
    # the CTA doesn't allow you to grab data about a specific alert
    # we have to crawl the page and parse... H T M L!
    # it blows
    # luckily - we have some beautiful soup. 
    def crawl_alert_update(self, alert_id=''):
        url = 'http://www.transitchicago.com/travel_information/alert_detail.aspx?AlertId=' + alert_id
        req = urllib2.Request(url)
        response = urllib2.urlopen(req)
        content = response.read()
        # this is the dirtiest and most annoying to quickly get this data. 
        # if you are interested in making this better. pleaes please please do. 
        content = content.split('<!-- start print content -->')
        content = content[1].split('<!-- end print content -->')[0]
        content = content.replace("\r",'')
        content = content.replace("\t",'')
        # i am sorry you have to see this. 

        impact_level = content.split('Impact Level:</h5>')[1].split('<h5>')[0]
        impact_level = self.remove_extra_spaces(impact_level)[1:]
        impact_level = self.remove_html_tags(impact_level)

        full_description = content.split('Full Description:</h5>')[1].split('</td>')[0]
        full_description = self.remove_extra_spaces(full_description)

        headline = content.split('<h2>')[1].split('</h2>')[0]
        headline = self.remove_extra_spaces(headline)[1:]

        duration = content.split('Length:</h5>')[1].split('<h5>')[0]
        duration = self.remove_extra_spaces(duration)[1:]
        duration = self.remove_html_tags(duration)
        duration = duration.split(' to ')

        alert_update = {
                'impact_level':impact_level,
                'headline':headline,
                'duration':duration,
                'full_description': full_description,
                
                }

        return alert_update 

if __name__ == "__main__": 
    c = CTAAlerts()
    status = c.route_status(route_id='')
    alerts = c.detailed_alerts(route_id='red')
    alert = c.crawl_alert_update('7362')
    print alert
