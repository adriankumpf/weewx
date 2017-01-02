import weewx
import weewx.engine
import weewx.wxformulas
import weewx.units

# assign various observations to the vapour group
weewx.units.obs_group_dict['dewpoint1'] = 'group_temperature'
weewx.units.obs_group_dict['dewpoint2'] = 'group_temperature'
weewx.units.obs_group_dict['dewpoint3'] = 'group_temperature'
weewx.units.obs_group_dict['dewpoint4'] = 'group_temperature'
weewx.units.obs_group_dict['roofTemp'] = 'group_temperature'

weewx.units.obs_group_dict['inDewpoint'] = 'group_temperature'

CF = 0.86897624

WC_C1 = 35.74
WC_C2 = 0.6215
WC_C3 = 35.75
WC_C4 = 0.4275
WC_E = 0.16

def vlimit(t):
    pow((WC_C1 - (1 - WC_C2) * t)/(WC_C3 - WC_C4 * t), 1/WC_E);

def tlimit(v):
    (WC_C1 - WC_C3 * pow(v, WC_E))/(1 - WC_C2 - WC_C4 * pow(v, WC_E));

def calculate_temperature(windchill, windspeed):
    if windchill is None or windspeed is None:
        return None

    if windchill >= 50.0 and windspeed < 3.0:
        return windchill

    if windchill < 50.0:
        vlim = vlimit(windchill);
        if windspeed < vlim:
            return windchill

    if windspeed >= 3.0:
        wlim = tlimit(windspeed)
        if windchill > wlim:
           return windchill

    ve = pow(windspeed, WC_E)
    result = (windchill + WC_C3 * ve - WC_C1) /	(WC_C4 * ve + WC_C2)

    if result < windchill:
        result = windchill

    return result

def calc_tempF(wc,v):
    if wc is  None or v is  None:
        t = None
    elif v < 3:
        t = wc
    else:
        t1 = 100 * (3575*v**(4/25) + 100*wc - 3574)
        t = t1 / (4275*v**(4/25) + 6214)

    return (t)

class ExtraCalculations(weewx.engine.StdService):
    def __init__(self, engine, config_dict):
        super(ExtraCalculations, self).__init__(engine, config_dict)
        self.bind(weewx.NEW_LOOP_PACKET, self.handle_new_loop)

    def handle_new_loop(self, event):
        # convert everything to US units for our calculations
        data_us = weewx.units.to_US(event.packet)

        # do the calculation for each item we want
        if 'extraTemp1' in data_us and 'extraHumid1' in data_us:
            data_us['dewpoint1'] = weewx.wxformulas.dewpointF(data_us['extraTemp1'], data_us['extraHumid1'])
        if 'extraTemp2' in data_us and 'extraHumid2' in data_us:
            data_us['dewpoint2'] = weewx.wxformulas.dewpointF(data_us['extraTemp2'], data_us['extraHumid2'])
        if 'extraTemp3' in data_us and 'extraHumid3' in data_us:
            data_us['dewpoint3'] = weewx.wxformulas.dewpointF(data_us['extraTemp3'], data_us['extraHumid3'])
        if 'extraTemp4' in data_us and 'extraHumid4' in data_us:
            data_us['dewpoint4'] = weewx.wxformulas.dewpointF(data_us['extraTemp4'], data_us['extraHumid4'])

        if 'windchill' in data_us and 'windSpeed' in data_us:
            data_us['roofTemp'] = calculate_temperature(data_us['windchill'], data_us['windSpeed'])

        if 'windSpeed' in data_us and data_us['windSpeed'] is not None:
            data_us['windSpeed_BF'] = weewx.wxformulas.beaufort(data_us['windSpeed'] * CF)

        # convert the packet back to the original unit system
        data_x = weewx.units.to_std_system(data_us, event.packet['usUnits'])

        # update the event packet with the new data
        event.packet.update(data_x)

