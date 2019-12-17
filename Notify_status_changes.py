import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import pyodbc
from datetime import datetime as dt
import base64
import logging
from getpass import getpass

ROOT_FOLDER = r'F:\Notify_Status_Changes'

logging.basicConfig(filename=os.path.join(ROOT_FOLDER, 'Notify_status_changes.log'), 
                    level=logging.DEBUG, 
                    format='%(asctime)s %(message)s')

SMTP_SERVER = 'us-smtp-outbound-1.mimecast.com' 
SMTP_PORT = 587
SENDER_EMAIL = 'donotreply@invenergyllc.com'

# for PRODUCTION only
SMTP_USERNAME = 'arcgisapp_notification@invenergyllc.com'
SMTP_PWD = None
SMTP_PWD = '%%%%%%%'

# for STAGING only
SMTP_USERNAME = 'arcgisapp_notification_test@invenergyllc.com' 
SMTP_PWD = None
SMTP_PWD = '*****'

# for LOGIC-dev only 
'''
SMTP_SERVER = 'smtp.office365.com' 
SMTP_USERNAME = 'cliang@invenergyllc.com'
SMTP_PWD = '$$$$$$$'
'''

QUERY_FIELD_LABELS = [
    'Project Name'
    ,'Project Status'
    ,'Developer'
    ,'APN'
    ,'APN2'
    ,'Land Agency'
    ,'Land Agent'
    ,'Land Agency'
    ,'Land Agent'
    ,'Previous Status'
    ,'Current Status'
    ,'Updated By'
    ,'Updated On'
]

SQLSERVER_HOST = 'az-cgissql1s'
SQLSERVER_DATABASE = 'INV_DEV_LAND'
QUERY_FIELD_NAMES = [
    'PROJECT_NAME'
    ,'PROJECT_STATUS'
    ,'DEVELOPER'
    ,'APN'
    ,'APN2'
    ,'LAND_AGENCY_1'
    ,'LAND_AGENT_1'
    ,'LAND_AGENCY_2'
    ,'LAND_AGENT_2'
    ,'OLD_STATUS'
    ,'NEW_STATUS'
    ,'last_edited_user'
    ,'last_edited_date'
]

SQL_QUERY = 'select ' + ','.join(QUERY_FIELD_NAMES) + '\
    from [dbo].[DEV_PROSPECT_STATUS_UPDATE_LOG] \
    where last_edited_date >= DATEADD(DAY,-1, CAST(GETDATE() AS DATE)) \
        and last_edited_date < DATEADD(DAY,1, CAST(GETDATE() AS DATE)) \
    order by PROJECT_NAME, APN, APN2'

HTML_STYLE_TABLE = 'style="border: 1px solid lightgrey;"'
HTML_STYLE_HEADER = 'style="border: 1px solid lightgrey;background-color:DarkBlue;color:white;"'
HTML_STYLE_ROW_ODD = 'style="border: 1px solid lightgrey;background-color:white;color:black;"'
HTML_STYLE_ROW_EVEN = 'style="border: 1px solid lightgrey;background-color:LightBlue;color:black;"'

msg_subject = "Important Parcel Status Updates [{0}]"
msg_body_text = """\
The following parcel(s) status has changed in the past 24 hours, please review:

{0}

Disclaimer: This email is generated and sent automatically. Please contact GIS Team for details.
"""

msg_body_html = """\
<html>
  <body>
    <p>
    The following parcel(s) status has changed in the past 24 hours, please review: 
    </p>
    <br>
    {0}
    <br>
    <p>
    Disclaimer: This email is generated and sent automatically. Please contact GIS Team for details.
    </p>
  </body>
</html>
"""

PWD_FILENAME = os.path.join(ROOT_FOLDER, 'pwd')


def compose_message_text(status_updates):
    message_text = "\n"
    # header-row
    for fd in QUERY_FIELD_LABELS: 
        message_text = message_text + ("" + fd + "\t")
    # content-row
    for su in status_updates:
        message_text = message_text + "\n"
        for fd in QUERY_FIELD_NAMES: 
            val = "" if su[fd] is None else su[fd]            
            message_text = message_text + ("" + val + "\t")
        message_text = message_text + "\n"
    message_text = message_text + "\n"
    return msg_body_text.format(message_text)


def compose_message_html(status_updates):
    message_html = "<table {0}>".format(HTML_STYLE_TABLE)
    # header-row
    for fd in QUERY_FIELD_LABELS: 
        cell_html = ("<th {0}>" + fd + "</th>").format(HTML_STYLE_HEADER)
        message_html = message_html + cell_html
    # content-row
    for u in range(0, len(status_updates)):
        su = status_updates[u]
        cell_html_style = (HTML_STYLE_ROW_EVEN if u % 2 == 0 else HTML_STYLE_ROW_ODD)
        message_html = message_html + "<tr>"
        for fd in QUERY_FIELD_NAMES:
            val = "" if su[fd] is None else su[fd] 
            cell_html = ("<td {0}>".format(cell_html_style) + val + "</td>").format(HTML_STYLE_HEADER)
            message_html = message_html + cell_html
        message_html = message_html + "</tr>"
    message_html = message_html + "</table>"
    return msg_body_html.format(message_html)


def get_password(): 
    pwd_path = os.path.join(ROOT_FOLDER, PWD_FILENAME)
    logging.debug('pwd_path: ' + pwd_path)
    if not os.path.exists(pwd_path): 
        pwd_text = getpass('Enter the password:')
        with open(pwd_path, 'w') as f: 
            f.write(base64.b64encode(pwd_text))
        os.system("attrib +h {0}".format(pwd_path))
    with open(pwd_path, 'r') as f: 
        pwd = f.read()
        return pwd
    

def remove_password():
    pwd_path = os.path.join(ROOT_FOLDER, PWD_FILENAME)
    if os.path.exists(pwd_path):
        os.remove(pwd_path)


def send_email(to_email, msg): 
    # Try to log in to server and send email
    try:
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.ehlo() # Can be omitted
        server.starttls() # Secure the connection
        server.ehlo() # Can be omitted
        server.login(SMTP_USERNAME, base64.b64decode(SMTP_PWD)) # 
        # TODO: Send email here
        server.sendmail(SENDER_EMAIL, to_email, str(msg))
        return True
    except Exception as e:
        logging.error('error in send_email: ' + str(e))
        remove_password()
        return False
    finally:
        if server is not None: 
            server.quit() 


def create_email(SMTP_USERNAME, receiver_email, message_text, message_html): 
    message = MIMEMultipart("alternative")
    message["Subject"] = msg_subject.format(dt.now().strftime('%Y-%m-%d'))
    message["From"] = 'donotreply@invenergyllc.com' # SMTP_USERNAME
    message["To"] = receiver_email

    # Turn these into plain/html MIMEText objects
    part1 = MIMEText(message_text, "plain")
    part2 = MIMEText(message_html, "html")

    # Add HTML/plain-text parts to MIMEMultipart message
    # The email client will try to render the last part first
    message.attach(part1)
    message.attach(part2)

    return message


def retrieve_status_updates(): 
    # retrieve the status updates from the database 
    # return an array 
    status_updates = []
    cnxn = None
    
    try: 
        cnxn = pyodbc.connect('DRIVER={SQL Server};SERVER='+SQLSERVER_HOST+';DATABASE='+SQLSERVER_DATABASE+';Trusted_Connection=yes;')
        cursor = cnxn.cursor()

        cursor.execute(SQL_QUERY)
        while 1:
            row = cursor.fetchone()
            if not row:
                break
            last_edited_date = ':'.join(row.last_edited_date.split(':')[:-1])
            status_updates.append({
                "PROJECT_NAME": row.PROJECT_NAME, 
                "PROJECT_STATUS": row.PROJECT_STATUS, 
                "DEVELOPER": row.DEVELOPER, 
                "APN": row.APN, 
                "APN2": row.APN2, 
                "LAND_AGENCY_1": row.LAND_AGENCY_1, 
                "LAND_AGENT_1": row.LAND_AGENT_1, 
                "LAND_AGENCY_2": row.LAND_AGENCY_2, 
                "LAND_AGENT_2": row.LAND_AGENT_2, 
                "OLD_STATUS": row.OLD_STATUS, 
                "NEW_STATUS": row.NEW_STATUS, 
                "last_edited_user": row.last_edited_user,
                "last_edited_date": last_edited_date
            })
    except Exception as e: 
        logging.error("Error in retrieve_status_updates: " + str(e))
    finally: 
        if cnxn is not None: 
            cnxn.close()

    return status_updates


if __name__ == "__main__":
    if SMTP_PWD is None: 
        SMTP_PWD = get_password()
    status_updates = retrieve_status_updates()
    if len(status_updates) == 0: 
        logging.info("No important status update. No email sent. ")
    else:
        status_updates_by_dev = {}
        for su in status_updates:
            receiver = su['DEVELOPER']
            if receiver not in status_updates_by_dev.keys(): 
                status_updates_by_dev[receiver] = []
            status_updates_by_dev[receiver].append(su)
        for dev in status_updates_by_dev.keys(): 
            msg_text = compose_message_text(status_updates_by_dev[dev])
            msg_html = compose_message_html(status_updates_by_dev[dev])
            email = create_email(send_email, dev, msg_text, msg_html)
            if send_email(dev, email) is True:
                logging.info('Sent an email to {0}'.format(dev))
            else:
                logging.error('Failed to send an email to {0}'.format(dev))
