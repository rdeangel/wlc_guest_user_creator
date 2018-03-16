#!/usr/bin/env python

"""Cisco WLC Wifi Guest User Creator

wlc_guest_user_creator - Version 1.3.2

Writte by Rocco De Angelis
"""

from __future__ import print_function
from netmiko import (
    ConnectHandler, NetMikoTimeoutException, NetMikoAuthenticationException)
import paramiko
import socket
import numpy as np
import csv
import os
import sys
import random
import re
import string
import configparser
from datetime import datetime
from datetime import timedelta
from time import sleep
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class email_SMTP(object):
    """Send text email via SMTP server
    """
    def __init__(self, host, sender_name=None, sender=None, receiver_name=None, receiver=None, subject=None, message=None):
        self.host = host
        self.sender_name = sender_name
        self.sender = sender
        self.receiver_name = receiver_name
        self.receiver = receiver
        self.subject = subject
        self.message = message
    
    def test(self):
        try:
            smtp_obj = smtplib.SMTP(self.host)
            smtp_test = smtp_obj.ehlo()
            smtp_obj.quit()

            if smtp_test[0] == 250:
                print('Reply Code: ' + str(smtp_test[0]) + ' OK')
                return True
            else:
                print('Reply Code: ' + str(smtp_test[0]) + ' UNKNOWN. (250 is required to continue)\nExiting!')
                return False
                
                
        except smtplib.SMTPException as e:
            print('Error: Unable to send email')
            return False
        except socket.error as e:
            print('Error: Could not connect to SMTP server - is it down or unreachable?\n({0})'.format(e.strerror))
            return False
        except:
            print('Unknown Error: ', sys.exc_info()[0])
            return False
    
    def send(self):
        mimemsg = MIMEMultipart('alternative')
        mimemsg['Subject'] = self.subject
        mimemsg['From'] = self.sender_name + " <" + self.sender + ">"
        mimemsg['To'] = self.sender_name + " <" + self.sender + ">"
        
        html_header = (
            '<html style=min-height: 100%; margin: 0;>\n'
            '  <head></head>\n'
            '  <bodyi style=min-height: 100%; margin: 0;>\n'
            '    <p><div style="display: block; font-family: Calibri,Candara,Segoe,Segoe UI,Optima,Arial,sans-serif; white-space: pre; font-size: 15px;">\n'
		)
        html_body = self.message.replace("\r\n", "<br>\n")
        html_body = html_body.replace("-\n", "-<br>\n")
        html_body = html_body.replace("|\n", "|<br>\n")
        html_trailer = (
            '   </div></p>\n'
            '  </body>\n'
            '</html>\n'
        )
        
        html = html_header + html_body + html_trailer
        #print(html)
        html_msg = MIMEText(html, 'html')
        
        # Attach parts into message container.
        # According to RFC 2046, the last part of a multipart message, in this case
        # the HTML message, is best and preferred.
        mimemsg.attach(html_msg)
        
        try:
            smtp_obj = smtplib.SMTP(self.host)
            smtp_obj.sendmail(self.sender, self.receiver, mimemsg.as_string())
            print('Successfully sent email')
            return True
        except smtplib.SMTPException as e:
            print('Error: Unable to send email')
            return False
        except socket.error as e:
            print('Error: Could not connect to SMTP server - is it down or unreachable?\n({0})'.format(e.strerror))
            return False
        except:
            print('Unknown Error: ', sys.exc_info()[0])
            return False


def script_start(print_time):
    if print_time:
        script_start_time = datetime.utcnow()
        script_start_formatted = script_start_time.strftime("%a %b %d %H:%M:%S GMT %Y")
        print('Script Start Time: ' + script_start_formatted)
        print('-' * 100)
        print('-' * 100)
        print('-' * 100)
        return script_start_time
    
def script_end():
    script_end_time = datetime.utcnow()
    script_end_formatted = script_end_time.strftime("%a %b %d %H:%M:%S GMT %Y")
    print('-' * 100)
    print('-' * 100)
    print('-' * 100)
    print('Script End Time: ' + script_end_formatted)
    print('\n\n\n')
    return script_end_time
    

def format_select_data(csv_data, entered_id, csv_file):

    id_idx = None
    id_list = []

    if len(csv_data) == 0:
        print('No job ids exist!')
    elif csv_data.ndim == 1:
        id_list.append(csv_data[0][0])
        id_idx = 0
    else:
        for i in range(len(csv_data)):
            id_list.append(csv_data[i][0])
            if str(entered_id) == csv_data[i][0]:
                id_idx = i

    if id_list.count(entered_id) > 1:
        print('Selected id ' + entered_id + ' is used more than once in the data file: ' + csv_file)
        print('Remove duplicate ids and run the script again!')
        print('-' * 100)
        return None

    if (id_idx == None) and (len(csv_data) != 0):
        print('-'*100)
        print('The selected id ' + str(entered_id) + ' doesn\'t exist!\n')
        return None

    if csv_data.ndim == 1:
        id = csv_data[0]
        wlc_ip = csv_data[1]
        wlc_name = csv_data[2]
        user_prefix = csv_data[3]
        user_qty = csv_data[4]
        wlan_id = csv_data[5]
        ssid = csv_data[6]
        user_type = csv_data[7]
        lifetime = csv_data[8]
        description = csv_data[9]
        guest_email_receiver_address = csv_data[10]
    elif csv_data.ndim > 1:
        id = csv_data[id_idx][0]
        wlc_ip = csv_data[id_idx][1]
        wlc_name = csv_data[id_idx][2]
        user_prefix = csv_data[id_idx][3]
        user_qty = csv_data[id_idx][4]
        wlan_id = csv_data[id_idx][5]
        ssid = csv_data[id_idx][6]
        user_type = csv_data[id_idx][7]
        lifetime = csv_data[id_idx][8]
        description = csv_data[id_idx][9]
        guest_email_receiver_address = csv_data[id_idx][10]
    else:
        print("Something has gone wrong!\n")
        return None

    if id == str(entered_id):
        password_length = 8
        chars = string.ascii_letters + string.digits + ''
        random.seed = (os.urandom(1024))
        command_list = []
        user_credentials = []
        #Generates a list of commands
        for i in range(int(user_qty)):
            user = user_prefix + '_' + str(i+1)
            password = ''.join(random.choice(chars) for i in range(password_length))
            command_del = 'config netuser delete username ' + user + ''
            command_add = 'config netuser add ' + user + ' ' + password + ' wlan ' + wlan_id + ' userType ' + user_type + ' lifetime ' + lifetime + ' description "' + description + '"'
            command_list.append(command_del)
            command_list.append(command_add)
            user_credentials.append([[user],[password]])
        selected_data = [id, wlc_ip, wlc_name, user_prefix, user_qty, wlan_id, ssid, user_type, lifetime, description, guest_email_receiver_address]
        #Returns list of commands
        return selected_data, command_list, user_credentials
    else:
        print(id, entered_id)
        print('The selected id ' + str(entered_id) + ' doesn\'t exist!\n')
        return None


        
def issue_commands_on_device(platform, wlc_name, wlc_ip, username, password, command_list):
    
    creation_outcome = ''
    cli_failure_msg = 'WLC cli commads execution failure, check script log file for command execution logs'
    
    try:
        device = ConnectHandler(device_type=platform, ip=wlc_ip, username=username, password=password)
        print('SSH Connected!\nExecuting the following commands via ssh on "' + wlc_name + ' - '  + wlc_ip + '":\n' + '-' * 100)
    
        for command in command_list:
            print(re.sub(r'(.*?config netuser add\ .*?\ )(.{8})(\ wlan.*?)', r'\1********\3', command, re.MULTILINE))
            command_result = device.send_command(command)
            if command_result == '\n':
                command_result = '\nNo Output\n\n'
                if creation_outcome != ('' or cli_failure_msg): creation_outcome = 'success'
            else:
                command_result = re.sub(r'(.*?user add\ .*?\ )(.{8})(\ wlan.*?)', r'\1********\3', command_result, re.MULTILINE)
                if (creation_outcome != ('' or cli_failure_msg)) and ((command_result == '\n') or ('Deleted user' in command_result) or (re.findall(r'.*?User.*?does\ not\ exist.*', command_result) is not None)):
                    creation_outcome = 'success'
                else:
                    creation_outcome = cli_failure_msg
            print('Command Output:\n' + ('-' * 100) + '\n' + command_result + '' + ('-' * 100) + '\n')
        
        print('save config')
        output = device.send_command('save config\ny')
        print(output)
    
        device.disconnect()
        return creation_outcome

    except NetMikoTimeoutException:
        err_msg = 'SSH connection timeout for %s (%s)' % (wlc_name, wlc_ip)
        print(err_msg)
        return err_msg
    except NetMikoAuthenticationException:
        err_msg = 'SSH authentication failure for %s (%s)' % (wlc_name, wlc_ip)
        print(err_msg)
        return err_msg
    except IOError:
        err_msg = 'SSH session ended unexpectedly for %s (%s)' % (wlc_name, wlc_ip)
        print(err_msg)
        return err_msg
    except Exception:
        err_msg = 'Unspecified exception for %s (%s). (Maybe wrong password or something else entirely)' % (wlc_name, wlc_ip)
        print(err_msg)
        return err_msg

    
def send_guest_user_mail(user_credentials, ssid, user_type, date_start, date_end, email_server, guest_email_sender_name, guest_email_sender_address, guest_email_receiver_address):
    
    guest_email_receiver_name = guest_email_receiver_address
    guest_email_subject = "Wireless Guest User Credentials"
    
    i = 0
    for user_credential in user_credentials:
        formatted_start_date = date_start.strftime("%a %b %d %H:%M:00 GMT %Y")
        formatted_end_date = date_end.strftime("%a %b %d %H:%M:00 GMT %Y")
        user, password = user_credential[0][0], user_credential[1][0]
        guest_email_msg = ('Wireless Guest User Credentials\n'
            '-------------------------------\n'
            'Guest account User Name : %s\n'
            'Guest account Password : %s\n'
            'Profile name : %s\n'
            'User Active from : %s User Active until : %s\n\n'
            'DISCLAIMER : Guests understand and acknowledge that we exercise no control over the nature, content or reliability of the information and/or data passing through our network.\n\n'
            'Regards,\n\n'
            'Network Team'
        ) % (user, password, ssid, formatted_start_date, formatted_end_date)
        #print(guest_email_msg)
        email = email_SMTP(email_server, guest_email_sender_name, guest_email_sender_address, guest_email_receiver_name, guest_email_receiver_address, guest_email_subject, guest_email_msg)
        email.send()
        i += 1


def send_generic_mail(email_server, admin_email_sender_name, admin_email_sender_address, admin_email_receiver_name, admin_email_receiver_address, admin_email_subject, admin_email_msg):
 
    email = email_SMTP(email_server, admin_email_sender_name, admin_email_sender_address, admin_email_receiver_name, admin_email_receiver_address, admin_email_subject, admin_email_msg)
    result = email.send()
    return result


def test_email_server(email_server):

    email = email_SMTP(email_server)
    result = email.test()
    return result


def main(argv):

    config_file = 'config.ini'

    try:
        config = configparser.ConfigParser()
        config.read(config_file)
        
        #load config files setting
        platform = config['DEVICE_PARAMETERS']['Platform']
        username = config['DEVICE_PARAMETERS']['Username']
        password = config['DEVICE_PARAMETERS']['Password']
        guest_email_sender_name = config['GUEST_USERS_EMAIL']['GuestEmailSenderName']
        guest_email_sender_address = config['GUEST_USERS_EMAIL']['GuestEmailSenderAddress']
        admin_email_sender_name  = config['ADMIN_NOTIFICATION_EMAIL']['AdminEmailSenderName']
        admin_email_sender_address = config['ADMIN_NOTIFICATION_EMAIL']['AdminEmailSenderAddress']
        admin_email_receiver_name = config['ADMIN_NOTIFICATION_EMAIL']['AdminEmailReceiverName']
        admin_email_receiver_address = config['ADMIN_NOTIFICATION_EMAIL']['AdminEmailReceiverAddress']
        csv_file = config['GLOBAL_PARAMETERS']['CsvFile']
        csv_rows_skip = config['GLOBAL_PARAMETERS']['CsvRowsSkip']
        email_server = config['GLOBAL_PARAMETERS']['EmailServer']
        file_logging = config['GLOBAL_PARAMETERS']['FileLogging']
        log_file_name = config['GLOBAL_PARAMETERS']['LogFileName']
    except:
        print('Error: it is not possible to read config from file: ' + config_file)
        sys.exit(0)
    users_email_qty_sent = 0
    email_admin_report = ''
    admin_email_msg = ''
    csv_exception_occurred = False
    id_list_pass = []
    
    if file_logging == 'False':
        file_logging = False 
    else: 
        file_logging = True

    if file_logging == True:
        fd = open(log_file_name,'a') # File logging location and name.
        sys.stdout = fd
        script_start_time = script_start(True)
    else:
        script_start_time = script_start(False)
    
    date_start = script_start_time
    
    print('Testing availability of SMTP server: ' + email_server)
    email_test_result = test_email_server(email_server)
    if email_test_result:
        print('-'*100)
    else:
        script_end()
        sys.exit(0)
    
    if len(argv) == 0:
        print('You need to enter at least one id argument!\n')
        script_end()
        sys.exit(0)
        
    for arg in argv:
        if (argv.count(arg)) > 1:
            print('Error: id ' + str(arg) + ' has ' + str(argv.count(arg)) + ' duplicates.')
            print('Duplicate script arguments are not allowed, remove them and run the script again.')
            script_end()
            fd.close()
            sys.exit(0)
        
    try:
        csv_loaded_data = np.loadtxt(csv_file, dtype=str, delimiter=',', skiprows=int(csv_rows_skip))
    except:
        print('Error: it is not possible to load data from file: ' + csv_file + '\n')
        csv_exception_occurred = True

    for argument in argv:
        try:
            selected_csv_data, commands, user_credentials = format_select_data(csv_loaded_data, argument, csv_file)
        except IndexError as e:
            if csv_exception_occurred != True:
                print('Error: it is not possible to load data from file: ' + csv_file + '\n{0}'.format(e))
                print('-'*100)
                csv_exception_occurred = True
            continue
        except:
            if csv_exception_occurred != True:
                print('Error: it is not possible to load data from file: ' + csv_file)
                print('-'*100)
                csv_exception_occurred = True
            continue

        id = selected_csv_data[0]
        wlc_ip = selected_csv_data[1]
        wlc_name = selected_csv_data[2]
        user_prefix = selected_csv_data[3]
        user_qty = selected_csv_data[4]
        wlan_id = selected_csv_data[5]
        ssid = selected_csv_data[6]
        user_type = selected_csv_data[7]
        lifetime = selected_csv_data[8]
        description = selected_csv_data[9]
        guest_email_receiver_address = selected_csv_data[10]
        date_end = date_start + timedelta(seconds=int(lifetime))
        
        #Execute commands to add users on WLCs
        print('Attempting to SSH to %s (%s) - Running job id: %s' % (wlc_name, wlc_ip, id))
        wlc_creation_result = issue_commands_on_device(platform, wlc_name, wlc_ip, username, password, commands)
        
        if wlc_creation_result == 'success':
            #when a job has run succesfully run code below
            
            #creating list of ids ran in this script execution
            id_list_pass.append(id)
            print('Wireless Guest users were successfully created')
            print('-'*100)
            
            #Send e-mail for each guest created
            print('\nSending e-mails to recipient: ' + guest_email_receiver_address + '\n' + '-' * 100) 
            send_guest_user_mail(user_credentials, ssid, 'guest', date_start, date_end, email_server, guest_email_sender_name, guest_email_sender_address, guest_email_receiver_address)
            print('-'*100)
            print('\n\n\n')
            
            #Formats wireless user creation e-mail that is later send out out to the Admin
            users_email_qty_sent += int(user_qty)
            email_admin_report += 'Guest users for job id ' + id + ' sent out to: ' + guest_email_receiver_address + '\nCreated on WLC: "' + wlc_name + ' - '  + wlc_ip + '"\n'
            user_count = 0
            for user_credential in user_credentials:
                email_admin_report = email_admin_report + 'Wifi User ' + str(user_count+1) + ': ' + str(user_credential[0][0]) + ' - Lifetime: ' + lifetime + ' seconds\n'
                user_count+=1
            email_admin_report += '\n'
            #adding continue below will generate a single Wireless Guest User Creation Report for Sucessful jobs
            #removing continue will generate multiple Wireless Guest User Creation Report for each Sucessful job
            continue
        else:
            #Job error in creation of Wireless Guest Users, e-mail and continue with next job id if any.
            err_msg = 'An error occurred in the Wireless Guest User Creation script.\n\nJob id ' + argument + ' failed due to the following reason:\n' + wlc_creation_result + '\n\n'
            err_msg += 'Job info:\n'
            err_msg += (
                'id = %s\n'
                'WLC IP = %s\n'
                'WLC Name = %s\n'
                'User Prefix = %s\n'
                'User Qty = %s\n'
                'WLAN id = %s\n'
                'SSID = %s\n'
                'User Type = %s\n'
                'Lifetime = %s\n'
                'Description = %s\n'
                'Email Recipient = %s\n'
            ) % (id, wlc_ip, wlc_name, user_prefix, user_qty, wlan_id, ssid, user_type, lifetime, description, guest_email_receiver_address)
            print('-'*100)
            print('\n\n')
            admin_email_subject = 'Error / Wireless Guest User Creation - job id ' + argument + ' failed.'
            admin_email_msg = err_msg
            print('\nSending e-mail to Admin Recipient: ' + admin_email_receiver_address + '\n' + admin_email_subject + '\n' + '-' * 100)
            print(admin_email_msg)
            print('-'*100)
            send_generic_mail(email_server, admin_email_sender_name, admin_email_sender_address, admin_email_receiver_name, admin_email_receiver_address, admin_email_subject, admin_email_msg)
            print('-'*100)
            print('\n\n\n')
    
    if users_email_qty_sent > 0:
        admin_email_msg = 'A total of %s guest e-mails have been sent out:\n\n' % (users_email_qty_sent)
        admin_email_msg = admin_email_msg + email_admin_report
        
        #Send Notification E-mail to Admin
        report_heading = "Wireless Guest User Creation Report for Sucessful Job Id: "
        id_list_pass_size = len(id_list_pass)
        for i in range(id_list_pass_size):
            if i < id_list_pass_size-1:
                report_heading += id_list_pass[i] + ', '
            else:
                report_heading += id_list_pass[i]
            i+=1
        print('\nSending e-mail to Admin Recipient: ' + admin_email_receiver_address + '\n' + report_heading + '\n' + '-' * 100)
        print(admin_email_msg)
        print('-'*100)
        admin_email_subject = report_heading
        send_generic_mail(email_server, admin_email_sender_name, admin_email_sender_address, admin_email_receiver_name, admin_email_receiver_address, admin_email_subject, admin_email_msg)
        print('-' * 100)

    if file_logging == True:
        script_end()
        fd.close()


if __name__ == "__main__":
    try:
        main(sys.argv[1:])
    except KeyboardInterrupt:
        print('\nInterrupted by CTRL-C')
        script_end()
        sys.exit(0)
