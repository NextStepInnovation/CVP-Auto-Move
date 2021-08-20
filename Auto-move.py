#!/usr/bin/env python3

import sys
import os
import requests
import yaml
from cvprac.cvp_client import CvpClient
import argparse
import ssl
import logging
ssl._create_default_https_context = ssl._create_unverified_context

def Main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cvp', default='192.168.101.26', help='CVP Server IP')
    parser.add_argument('--username', default='cvpadmin', help='CVP username')
<<<<<<< Updated upstream
    parser.add_argument('--password', default='', help='CVP password')
=======
    parser.add_argument('--password', default='$3cr3t$3cr3t', help='Cloudvision password')
>>>>>>> Stashed changes
    parser.add_argument('--logging', default='', help='Logging levels info, error, or debug')
    parser.add_argument('--devlist', default='devices.yml', help='YAML file with list of approved devices.')
    args = parser.parse_args()

    # Only enable logging when necessary
    if args.logging != '':
        logginglevel = args.logging
        formattedlevel = logginglevel.upper()

        # Open logfile
        logging.basicConfig(format='%(asctime)s %(levelname)-8s %(message)s',filename='cvpmove.log', level=formattedlevel, datefmt='%Y-%m-%d %H:%M:%S')
    else:
        ()

    # Open YAML variable file
    with open(os.path.join(sys.path[0],args.devlist), 'r') as vars_:
        data = yaml.safe_load(vars_)
    
    # CVPRAC connect to CVP
    clnt = CvpClient()
    try:
        clnt.connect(nodes=[args.cvp], username=args.username, password=args.password)
    except:
        logging.error('Unable to login to Cloudvision')

    # Get devices from Undefined container in CVP and add their MAC to a list
    undefined = clnt.api.get_devices_in_container('Undefined')
    undef = []
    for unprov in undefined:
        undef.append(unprov['systemMacAddress'])

    # Compare list of devices in CVP undefined container to list of approved devices defined in YAML file
    # If the the device is defined in the YAML file then provision it to the proper container
    tasks = []
    for dev in data['all']:
        if dev['mac'] in undef:
            device = clnt.api.get_device_by_mac(dev['mac'])
            try:
                tsk = clnt.api.deploy_device(device=device, container=dev['container'])
                Execute(clnt, tsk['data']['taskIds'])
                con = Configlet(clnt, dev, args.cvp, args.username, args.password)
                if con != None and con != 'reconcile':
                    assign = AssignConfiglet(clnt, dev, con)
                    Execute(clnt, assign['data']['taskIds'])
                elif con == 'reconcile':
                    cfglets = Containercfg(clnt, dev)
                    Execute(clnt, cfglets['data']['taskIds'])
                else:
                    logging.info('Configlet already exist.')
            except:
                logging.error('Unable to deploy device.')
        else:
            logging.info('device ' + str(undef) + ' not approved for deployment or already provisioned.')

    # Run the task using the Execute function
    Execute(clnt, tasks)


# Function to create configlet for management
def Configlet(clnt, data, cvp, user, password):
    l = []
<<<<<<< Updated upstream
    config = clnt.api.get_configlets(start=0, end=0)
=======
    try:
        config = clnt.api.get_configlets(start=0, end=0)
        ztp = clnt.api.get_device_by_mac(data['mac'])
    except:
        logging.error('Unable to get list of configlets.')

>>>>>>> Stashed changes
    for configlet in config['data']:
        l.append(configlet['name'])
    
    if data['hostname'] + str('_mgmt') in l:
        logging.info('Configlet ' + str(data['hostname'] + '_mgmt') + ' already exist')
    elif ztp['ztpMode'] == 'true':
        try:
            cfglt = clnt.api.add_configlet(name=data['hostname'] + str('_mgmt'), config='hostname ' + str(data['hostname']) + '\ninterface management1\nip address ' + str(data['ip']) + '/24\nno shut\nip route 0.0.0.0/0 ' + str(data['mgmtgateway']) + '\ndaemon TerminAttr\nexec /usr/bin/TerminAttr -ingestgrpcurl=192.168.101.26:9910 -cvcompression=gzip -ingestauth=key,arista -smashexcludes=ale,flexCounter,hardware,kni,pulse,strata -ingestexclude=/Sysdb/cell/1/agent,/Sysdb/cell/2/agent -ingestvrf=default -taillogs\nno shut')
            return cfglt
        except:
            logging.error('Unable to create configlet ' + str(data['hostname'] + '_mgmt'))
    else:
        try:
            container = clnt.api.get_container_by_name(name=data['container'])
            ckey = container['key']
            login = 'https://{server}/cvpservice/login/authenticate.do'.format(server=cvp)
            resp = requests.post(login, headers={'content-type': 'application/json'}, json={'userId': user, 'password': password}, verify=False)
            jresp = resp.json()
            token = jresp['cookie']['Value']
            url = 'https://{server}/cvpservice/provisioning/containerLevelReconcile.do?containerId={container}&reconcileAll=false'.format(server=cvp, container=ckey)
            response = requests.get(url, auth=(user, password), headers={'Cookie': 'access_token=' + str(token)}, verify=False)
            if response.status_code == 200:
                reconcile = 'reconcile'
            return reconcile
        except:
            logging.error('Unable to reconcile container.')


# function to assign configlet to new device
def AssignConfiglet(clnt, dev, con):
    device = clnt.api.get_device_by_mac(dev['mac'])
    cfglets = [{'name': dev['hostname'] + '_mgmt', 'key': con}]
    task = clnt.api.apply_configlets_to_device(app_name='mgmt_configlet', dev=device, new_configlets=cfglets)
    return task


def Containercfg(clnt, data):
    cfglets = clnt.api.get_configlets_by_device_id(data['mac'])
    cfglist = []
    for configlet in cfglets:
        cfglist.append({'name': configlet['name'], 'key': configlet['key']})
    device = clnt.api.get_device_by_mac(data['mac'])
    task = clnt.api.apply_configlets_to_device(app_name='container_configlet', dev=device, new_configlets=cfglist)
    return task


# Function to run task if they are for the devices we provisioned
def Execute(clnt, tasks):
    for task in tasks:
        try:
            clnt.api.execute_task(task_id=task)
        except:
            logging.info('Task ID ' + str(task) + ' is ' + ' failed to execute.')
    

if __name__ == '__main__':
   Main()