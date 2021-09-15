# CYBERSECURITY AUTOMATION PROGRAMMING ASSIGNMENT #
## files

* whois.py: python script, it request for domains data from whoisxmlapi, analyzes the info and send an email if needed.
* dockerfile: file to build the docker image
* crontab: to execute the script every day, and when the docker machine is started.
* requirements.txt: python packages needed to run the script.
* yesterday.pic: this file is created the first time the script is run. It stores the provided info from whoisxmlapi.
* appSettings.yaml: script settings that shouldn't be published in public sities like github with the credentials like mail sender or api key.

## executing script

  Build the docker machine and start it.  
  Note: please set the key api for whoisxmlapi and the e-mail account credentials first before building the image.  
  You need to set those parameters in appSettings.yaml:
  
  * whoisApiKey: api key for whoisxmlapi
  * senderMail: email used to send the notifications by e-mail.
  * senderPassword: sender email password.
  * smtpServer: default is 'smtp.gmail.com'
  * smtpPort: default is 587
  * recipients: array to store the mail addresses, used to send the updated info. Don't forget to set it!
  