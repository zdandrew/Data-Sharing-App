import boto3
from pdaota import app, mongo
from botocore.exceptions import ClientError
from pdaota.lib import *
from jinja2 import Environment, PackageLoader, select_autoescape

def verify_auth_token(token):
    s = Serializer(app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None

    key = {"email" : user_id}
    user = mongo.db.users.find_one(key)
    return user

# def send_auth_email(site_email):
#     token = get_auth_token(site_email)
#     msg = Message('PDA-OTA User Confirmation',
#                   sender='do-not-reply.pda-ota@gmail.com',
#                   recipients=[site_email])
#     msg.body = f'''To verify your email, please click the following link:

# { url_for('verifyuser', token=token, _external=True) }

# If you did not make this request, please disregard this email.
# '''
#     mail.send(msg)

# def send_pw_email(site_email, new_pw):
#     token = get_auth_token(site_email)
#     msg = Message('PDA-OTA Password Reset',
#                   sender='do-not-reply.pda-ota@gmail.com',
#                   recipients=[site_email])
#     msg.body = f'''Your password has temporarily been reset to {new_pw.decode('UTF-8')}.

# To reset your password, please click the following link:

# { url_for('resetpassword', token=token, _external=True) }

# If you did not make this request, please disregard this email.
# '''
#     mail.send(msg)

@app.route("/send_invitation_email/<string:recipients>/<string:lead_site>/<string:project>/<string:join_code>", methods=['GET', 'POST'])
def send_invitation_email(recipients, lead_site, project, join_code):
    try:
        recipients = recipients.split(",")

        print(recipients)

        send_template_email(subject = "PDA-OTA Project '"+ project +"'",
                            recipients = recipients,
                            template = "invite.html",
                            lead_site = lead_site,
                            project = project,
                            join_code = join_code)

        return "email successful!"
    except:
        return sys.exc_info()

def get_email_template(template, **kwargs):
    env = Environment(
        loader=PackageLoader('pdaota', 'email'),
        autoescape=select_autoescape(['html', 'xml'])
    )

    template_retrieved = env.get_template(template)

    return template_retrieved.render(**kwargs)

def send_template_email(subject, recipients, template, **kwargs):
    email_body = get_email_template(template, **kwargs)

    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "PDA-OTA <do.not.reply.pdamethods@gmail.com>"

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = recipients

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = subject

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "non-html!"
                
    # The HTML body of the email.
    BODY_HTML = email_body          

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': 
                    RECIPIENT,
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent!")

def send_email(subject, body, recipient):
    # Replace sender@example.com with your "From" address.
    # This address must be verified with Amazon SES.
    SENDER = "Hai-Shuo <haishuo@gmail.com>"

    # Replace recipient@example.com with a "To" address. If your account 
    # is still in the sandbox, this address must be verified.
    RECIPIENT = recipient

    # Specify a configuration set. If you do not want to use a configuration
    # set, comment the following variable, and the 
    # ConfigurationSetName=CONFIGURATION_SET argument below.
    # CONFIGURATION_SET = "ConfigSet"

    # If necessary, replace us-west-2 with the AWS Region you're using for Amazon SES.
    AWS_REGION = "us-east-1"

    # The subject line for the email.
    SUBJECT = subject

    # The email body for recipients with non-HTML email clients.
    BODY_TEXT = "non-html!"
                
    # The HTML body of the email.
    BODY_HTML = body          

    # The character encoding for the email.
    CHARSET = "UTF-8"

    # Create a new SES resource and specify a region.
    client = boto3.client('ses',region_name=AWS_REGION)

    # Try to send the email.
    try:
        #Provide the contents of the email.
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    RECIPIENT,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': CHARSET,
                        'Data': BODY_HTML,
                    },
                    'Text': {
                        'Charset': CHARSET,
                        'Data': BODY_TEXT,
                    },
                },
                'Subject': {
                    'Charset': CHARSET,
                    'Data': SUBJECT,
                },
            },
            Source=SENDER,
            # If you are not using a configuration set, comment or delete the
            # following line
            # ConfigurationSetName=CONFIGURATION_SET,
        )
    # Display an error if something goes wrong. 
    except ClientError as e:
        print(e.response['Error']['Message'])
    else:
        print("Email sent!")

