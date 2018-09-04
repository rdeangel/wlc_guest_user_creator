wlc_guest_user_creator
============================================================
Cisco WLC Wifi Guest User Creator


Download wlc_guest_user_creator from git
---------------------------------

	sudo git clone https://github.com/rdeangel/wlc_guest_user_creator wlc_guest_user_creator
	
or

	download https://github.com/rdeangel/wlc_guest_user_creator/archive/master.zip



config.ini
---------------------------------

Example Script configuration file:

	[DEVICE_PARAMETERS]
	Platform = cisco_wlc (do not change this value)
	Username = wlc administrator username
	Password = wlc administrator password

	[GUEST_USERS_EMAIL]
	GuestEmailSenderName = sender name for guest e-mails
	GuestEmailSenderAddress = sender e-mail address for guest e-mails

	[ADMIN_NOTIFICATION_EMAIL]
	AdminEmailSenderName = sender name for admin e-mails
	AdminEmailSenderAddress = sender e-mail address for admin e-mails
	AdminEmailReceiverName = receiver name for admin e-mails, multiple semicolon separated email receiver names can be added
	AdminEmailReceiverAddress = receiver e-mail address for admin e-mails, multiple semicolon separated email receiver addresses can be added

	[GLOBAL_PARAMETERS]
	CsvFile = filename where job data is stored
	CsvRowsSkip = number of top row to skip before job data starts
	EmailServer = IP of smtp server
	FileLogging = if file logging set this value to True, for terminal logs set it to False
	LogFileName = filename where logs will be written if FileLogging is set to True

	
	
job_data.csv
---------------------------------

Job ID definition file:

	id   		Job id (taken as argument by the script)
	wlcIP   	WLC IP where the guest accounts need to be created
	wlcName   	Hostname of WLC
	user_prefix 	User prefix test used for creation of users (_1 _2 _3 etc will be appended to each user created)
	userQty   	Number of users created using the user_prefix text
	wlanId   	WlanId of SSID on WLC
	ssid   		Guest SSID Name
	userType   	This is always guest, do not change
	lifetime   	Lifetime of guest user in seconds starting from creation of user
	timezone	Covert Active from and Active Until time in guest user credential e-mail and shows timezone + offset
	description   	Description of users created
	email   	Email address or recipient that will receive the SSID email with username and password


	
wlc_guest_user_creator.log
---------------------------------

If FileLogging is set to True in config.ini you will get details log entries of creation process, e-mails sent and any errors.

Location of log file and file name can be changed by changing the value of LogFileName in config.ini



Install required python libraries
---------------------------------

Depending on the python distribution you have on your system make sure you install all needed python libraries:

You will probably need to install the following:

	pip install paramiko
	pip install netmiko
	pip install numpy
	pip install configparser
	pip install pytz
	...maybe more or less packages installation are required depending on your installation of python3



Job Scheduling
---------------------------------

Scheduling of jobs needs to be done via linux cronjob or windows task scheduler



Running wlc_guest_user_creator.py
---------------------------------

One or more job id argument defined in job_data.csv are required by the script to run successfully.

Example of running 3x job in the same script execution or schedule:

    python wlc_guest_user_creator.py JOB-ID1 JOB-ID2 JOB-ID3

	


