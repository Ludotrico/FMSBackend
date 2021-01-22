import smtplib
from email.message import EmailMessage


EMAIL = "findmysupplyapp@gmail.com"
PSW = "


def customizeHtmlVerifContent(user, token):
    htmlContent = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
    
    </head>
    <body style="font-family: Open Sans, Helvetica">
    
        <table align="center"  style="max-width: 400px">
    
    
            <tr align="center"  >
                <td>
                    <a href="https://www.instagram.com/FindMySupply"   style="text-decoration: none">
                        <img src="http://drive.google.com/uc?export=view&id=1Qib85nxMxcwQfL7ouYNc6WG7Fa8JjgGz" width="120" height="120"/>
                    </a>
                </td>
    
    
            <tr align="left"  >
                <td>
                    <p>
                        <br> <br>Hi %s,
                        <br> <br>You’re almost done! Tap the email verification link below to finish setting up your Find My Supply account:<br>
                    </p>
                </td>
            </tr>
    
    
    
            <tr align="center">
                <td>
                    <a href=%s>
                        <button style="background-color: #ebda00;  color: black; font-size: 30px;   padding: 10px 10px;  border-radius: 15px; border: 3px solid white"   >
                        VERIFY EMAIL
                        </button>
                    </a>
                </td>
            </tr>
    
    
            <tr align="left"  >
                <td>
                    <br><p>Like what we do? Follow us:</p>
                </td>
            </tr>
    
    
            <tr align="center"  >
                <td>
                    <a href="https://www.twitter.com/FindMySupply" style="text-decoration: none">
                        <img src="http://drive.google.com/uc?export=view&id=1BWOvgTyrgIm2zx_OWf_RLC5opPZPvzgo" width="35" height="35"/>
                    </a>
    
    
                    <a href="https://www.facebook.com/FindMySupplyApp"  style="text-decoration: none">
                        <img  style="margin:0px 10px" src="http://drive.google.com/uc?export=view&id=1Uf7K2pRPyQt_udalWUD-jK9dnEIQYvJa" width="35" height="35"/>
                    </a>
    
    
    
    
                    <a href="https://www.instagram.com/FindMySupply"  style="text-decoration: none">
                        <img src="http://drive.google.com/uc?export=view&id=1Jr_mnl2B9TmLxm0h1gAmEcjiqkduxiAj" width="35" height="35"/>
                    </a>
                </td>
    
            </tr>
    
    
    
    
    
    
    
    
    
            <tr align="left"  >
                <td>
                    <br>Sincerely,<br><br>Find My Supply Team<br>
                </td>
            </tr>
    
    
            <tr align="center">
                <td>
                    <br>
                    <hr style="height:1px;border-width:0;color:gray;background-color:gray">
                </td>
            </tr>
    
    
            <tr align="center">
                <td>
                  Copyright © 2020 Find My Supply, 1731 Embarcadero, Palo Alto, CA 94303. All rights reserved.<br>
                </td>
    
            </tr>
    
    
    
    
    
            </tr>
        </table>
    
    </body>
    </html>
    ''' % (user.firstName, f"https://find-my-supply-274702.uc.r.appspot.com/verifyUser/{user.id}/{token}")     #f"http://127.0.0.1:8000/verifyUser/{userID}/{token}"

    return htmlContent


def customizeHtmlResetPswContent(user):
    htmlContent = '''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">

    </head>
    <body style="font-family: Open Sans, Helvetica">

        <table align="center"  style="max-width: 400px">


            <tr align="center"  >
                <td>
                    <a href="https://www.instagram.com/FindMySupply"   style="text-decoration: none">
                        <img src="http://drive.google.com/uc?export=view&id=1Qib85nxMxcwQfL7ouYNc6WG7Fa8JjgGz" width="120" height="120"/>
                    </a>
                </td>


            <tr align="left"  >
                <td>
                    <p>
                        <br> <br>Hi %s,
                        <br> <br>Looks like you forgot your password but that's ok! Tap the verification link below to change your password:<br>
                    </p>
                </td>
            </tr>



            <tr align="center">
                <td>
                    <a href=%s>
                        <button style="background-color: #ebda00;  color: black; font-size: 30px;   padding: 10px 10px;  border-radius: 15px; border: 3px solid white"   >
                        CHANGE PASSWORD
                        </button>
                    </a>
                </td>
            </tr>


            <tr align="left"  >
                <td>
                    <br><p>Like what we do? Follow us:</p>
                </td>
            </tr>


            <tr align="center"  >
                <td>
                    <a href="https://www.twitter.com/FindMySupply" style="text-decoration: none">
                        <img src="http://drive.google.com/uc?export=view&id=1BWOvgTyrgIm2zx_OWf_RLC5opPZPvzgo" width="35" height="35"/>
                    </a>


                    <a href="https://www.facebook.com/FindMySupplyApp"  style="text-decoration: none">
                        <img  style="margin:0px 10px" src="http://drive.google.com/uc?export=view&id=1Uf7K2pRPyQt_udalWUD-jK9dnEIQYvJa" width="35" height="35"/>
                    </a>




                    <a href="https://www.instagram.com/FindMySupply"  style="text-decoration: none">
                        <img src="http://drive.google.com/uc?export=view&id=1Jr_mnl2B9TmLxm0h1gAmEcjiqkduxiAj" width="35" height="35"/>
                    </a>
                </td>

            </tr>









            <tr align="left"  >
                <td>
                    <br>Sincerely,<br><br>Find My Supply Team<br>
                </td>
            </tr>


            <tr align="center">
                <td>
                    <br>
                    <hr style="height:1px;border-width:0;color:gray;background-color:gray">
                </td>
            </tr>


            <tr align="center">
                <td>
                  Copyright © 2020 Find My Supply, 1731 Embarcadero, Palo Alto, CA 94303. All rights reserved.<br>
                </td>

            </tr>





            </tr>
        </table>

    </body>
    </html>
    ''' % (user.firstName, f"https://find-my-supply-274702.uc.r.appspot.com/resetPassword/{user.id}")

    return htmlContent


def sendVerificationEmail(user, token):
    msg = EmailMessage()
    msg['Subject'] = "Email Verification"
    msg['From'] = "Find My Supply"
    msg['To'] = user.email


    #msg.set_content(f"Hi Ludovico,\nYou’re almost done! Tap the email verification link below to finish setting up your Find My Supply account:\n\nSincerely,\nThe Team")

    #htmlContent = open("findMySupply/Emails/verificationEmail.html").read()

    msg.add_alternative(customizeHtmlVerifContent(user, token), subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL, PSW)
        smtp.send_message(msg)

    print("Sent email")

def sendResetPasswordEmail(user):
    msg = EmailMessage()
    msg['Subject'] = "Reset Password"
    msg['From'] = "Find My Supply"
    msg['To'] = user.email



    msg.add_alternative(customizeHtmlResetPswContent(user), subtype='html')

    with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
        smtp.login(EMAIL, PSW)
        smtp.send_message(msg)

    print("Sent email")


