��    ?                          �     P   �  �     �   �  �   a  �   �  �   �  �  ;	  �   �
  :  r    �  �   �  �   �    �  �  �  �  O  &  �  f    x   ~  4  �  C   ,  "   p  �   �  �   7  x   �  1   R  �   �     3     A     S     _     r     y     }     �     �     �  	   �  	   �     �                 (        G     M     U     a     s     �     �  	   �     �     �     �     �     �        3   "      V   1   p   �  �     2"  �   ;#  P   �#  �   A$  �   �$  �   �%  �   "&  �   �&  �  `'  �   �(  :  �)    �*  �   �+  �   �,    �-  �  �1  �  t3  &  5  f  <6  x   �7  4  8  C   Q9  "   �9  �   �9  �   \:  x   �:  1   w;  �   �;     X<     f<     x<     �<     �<     �<     �<     �<     �<     �<  	   =  	   =     =     &=     3=     ;=  (   C=     l=     r=     z=     �=     �=     �=     �=  	   �=     �=     �=     >     >     $>     D>  3   G>     {>  1   �>   

<h2>Welcome to %(site_name)s,</h2>

<p>You recently signed up for <a href="%(site_url)s">%(site_name)s</a>.</p>

<p>Please confirm the e-mail address and get your password by clicking on this link:</p>

<a href="%(verification_link)s">%(verification_link)s</a>

 

Welcome to %(site_name)s,

You recently signed up for %(site_name)s.

Please confirm the e-mail address and get your password by clicking on this link:

  %(verification_link)s

 
          <p>Access cannot be granted at this time. Please try again later.</p> 
          <p>Access to the requested service could not be granted.
              The service might have requested a 'confirmed' identity.</p> 
          <p>Access to the requested service could not be granted.
              The service provider requires use of a 'confirmed' Security Key (SWAMID MFA/MFA HI).
          </p> 
          <p>Access to the requested service could not be granted.
              The service provider requires use of a Security Key (MFA).
          </p> 
          <p>The password has expired, because it had not been used in 18 months.</p>
	  <p>To regain access to the account, a reset of the credential is necessary.</p>
	   
          <p>This user account has been terminated.</p>
	  <p>To regain access to the account, a reset of the credential is necessary.</p>
	   
    <p>Hi,</p>
    <p>You are invited to join the group %(group_display_name)s with your <a href=%(site_url)s>%(site_name)s</a> account.</p>
    <p>To accept or decline the invitation go to <a href=%(group_invite_url)s>%(group_invite_url)s</a>.</p>
    <p>If you do not have an %(site_name)s account you can <a href="%(site_url)s">create one</a>.</p>
    <p>(This is an automated email. Please do not reply.)</p>
 
    <p>Hi,</p>
    <p>Your invite to the group %(group_display_name)s was canceled.</p>
    <p>(This is an automated email. Please do not reply.)</p>
 
    <p>You have chosen to terminate your account at <a href="%(site_url)s">%(site_name)s</a>.</p>

    <p><strong>If you did not initiate this action please reset your password immediately.</strong></p>

    <p>Thank you for using %(site_name)s.</p>

    <p>(This is an automated email. Please do not reply.)</p>
 
    <p>You have tried to verify your account at <a href="%(site_url)s">%(site_name)s</a>.</p>
    <p>We encountered a problem and kindly ask you to verify you account again using a different verification method.</p>
    <p>We apologize for any inconvenience.</p>
 
    You have chosen to terminate your account at %(site_name)s.

    If you did not initiate this action please reset your password immediately.

    Thank you for using %(site_name)s.

    (This is an automated email. Please do not reply.)
 
    You have tried to verify your account at %(site_name)s

    We encountered a problem and kindly ask you to verify you account again using a different verification method.

    We apologize for any inconvenience.
 
<div id="text_frame" style="font-size: 12pt">
    <h4>Welcome to confirm your eduID account</h4>

    <div id="notice-frame">
        <div style="padding-top: 15px; margin-left: 15px;">
            Username: %(recipient_primary_mail_address)s<br/>
            Code: %(recipient_verification_code)s<br/>
            <strong>The code is valid until %(recipient_validity_period)s.</strong><br/>
        </div>
    </div>
    <div style="padding-top: 50px;">
        <strong>Instructions:</strong>
    </div>
    <ol>
        <li>Log in to https://dashboard.eduid.se with the username above and the
            password you used when you created your account.
        </li>
        <li>Open the tab "Identity".</li>
        <li>Click "BY POST" below "Swedish personal ID number".</li>
        <li>Click "PROCEED" and input the code from this letter.</li>
        <li>Click "OK".</li>
    </ol>
    <div style="padding-top: 50px;">
        If you did not request this letter from eduID then please report it to support@eduid.se.
    </div>
</div>
 
<p>Hi,</p>
<p>You recently asked to reset your password for your %(site_name)s account.</p>
<p>To change your password, click the link below:</p>
<p><a href="%(reset_password_link)s">%(reset_password_link)s</a></p>
<p>If clicking the link does not work you can copy and paste it into your browser.</p>
<p>The password reset link is valid for %(password_reset_timeout)s hours.</p>
<p>(This is an automated email. Please do not reply.)</p>
 
<p>Thank you for registering with <a href="%(site_url)s">%(site_name)s</a>.</p>

<p>To confirm that you own this email address, simply click on the following link:

<a href="%(verification_link)s">%(verification_link)s</a></p>

<p>If clicking on the link above does not work, go to your profile and emails section. Click on the
confirmation icon and enter the following code:</p>

<p><strong>%(code)s</strong></p>

 
Hi,

You are invited to join the group %(group_display_name)s with your %(site_name)s account.

To accept or decline the invitation go to %(group_invite_url)s.

If you do not have an %(site_name)s account you can create one at
%(site_url)s.

(This is an automated email. Please do not reply.)
 
Hi,

You recently asked to reset your password for your %(site_name)s account.

To change your password, click the link below:

%(reset_password_link)s

If clicking the link does not work you can copy and paste it into your browser.

The password reset link is valid for %(password_reset_timeout)s hours.

(This is an automated email. Please do not reply.)
 
Hi,

Your invite to the group %(group_display_name)s was canceled.

(This is an automated email. Please do not reply.)
 
Thank you for registering with %(site_name)s.

To confirm that you own this email address, simply click on the following link:

%(verification_link)s

If clicking on the link above does not work, go to your profile and emails section. Click on the
verification icon and enter the following code:

%(code)s

 
This is your code for %(site_name)s.

Code: %(verification_code)s
 %(site_name)s account verification <p>Please try again.</p>
          <p>There is a link (Forgot your password?) on the login page if you do not remember
              your username or password.</p> <p>Sorry, but the requested page is unavailable due to a server hiccup.</p>
          <p>Our engineers have been notified already, so please try again later.</p> <p>The login request could not be processed.</p>
          <p>Try emptying the browsers cache and re-initiate login.</p> <p>The requested resource could not be found.</p> <p>You are already logged in.</p>
          <p>If you got here by pressing 'back' in your browser,
              you can press 'forward' to return to where you came from.</p> Access denied Already logged in Bad Request Credential expired Email: FAQ Forgot your password? Group invitation Group invitation cancelled Incorrect username or password Not Found Password: Reset password Server Error Sign in Sign up Something failed, or Javascript disabled Staff Student Technicians Terminate account Too many requests User terminated Username or password incorrect Visit the eduID Login eduID confirmation email eduID dashboard eduID login eduid-signup verification email en to confirm your Security Key (on the Security tab). to confirm your identity. to register a Security Key (on the Security tab). Project-Id-Version: PROJECT VERSION
Report-Msgid-Bugs-To: EMAIL@ADDRESS
POT-Creation-Date: 2022-10-26 12:45+0200
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: en
Language-Team: en <LL@li.org>
Plural-Forms: nplurals=2; plural=(n != 1);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.10.3
 

<h2>Welcome to %(site_name)s,</h2>

<p>You recently signed up for <a href="%(site_url)s">%(site_name)s</a>.</p>

<p>Please confirm the e-mail address and get your password by clicking on this link:</p>

<a href="%(verification_link)s">%(verification_link)s</a>

 

Welcome to %(site_name)s,

You recently signed up for %(site_name)s.

Please confirm the e-mail address and get your password by clicking on this link:

  %(verification_link)s

 
          <p>Access cannot be granted at this time. Please try again later.</p> 
          <p>Access to the requested service could not be granted.
              The service might have requested a 'confirmed' identity.</p> 
          <p>Access to the requested service could not be granted.
              The service provider requires use of a 'confirmed' Security Key (SWAMID MFA/MFA HI).
          </p> 
          <p>Access to the requested service could not be granted.
              The service provider requires use of a Security Key (MFA).
          </p> 
          <p>The password has expired, because it had not been used in 18 months.</p>
	  <p>To regain access to the account, a reset of the credential is necessary.</p>
	   
          <p>This user account has been terminated.</p>
	  <p>To regain access to the account, a reset of the credential is necessary.</p>
	   
    <p>Hi,</p>
    <p>You are invited to join the group %(group_display_name)s with your <a href=%(site_url)s>%(site_name)s</a> account.</p>
    <p>To accept or decline the invitation go to <a href=%(group_invite_url)s>%(group_invite_url)s</a>.</p>
    <p>If you do not have an %(site_name)s account you can <a href="%(site_url)s">create one</a>.</p>
    <p>(This is an automated email. Please do not reply.)</p>
 
    <p>Hi,</p>
    <p>Your invite to the group %(group_display_name)s was canceled.</p>
    <p>(This is an automated email. Please do not reply.)</p>
 
    <p>You have chosen to terminate your account at <a href="%(site_url)s">%(site_name)s</a>.</p>

    <p><strong>If you did not initiate this action please reset your password immediately.</strong></p>

    <p>Thank you for using %(site_name)s.</p>

    <p>(This is an automated email. Please do not reply.)</p>
 
    <p>You have tried to verify your account at <a href="%(site_url)s">%(site_name)s</a>.</p>
    <p>We encountered a problem and kindly ask you to verify you account again using a different verification method.</p>
    <p>We apologize for any inconvenience.</p>
 
    You have chosen to terminate your account at %(site_name)s.

    If you did not initiate this action please reset your password immediately.

    Thank you for using %(site_name)s.

    (This is an automated email. Please do not reply.)
 
    You have tried to verify your account at %(site_name)s

    We encountered a problem and kindly ask you to verify you account again using a different verification method.

    We apologize for any inconvenience.
 
<div id="text_frame" style="font-size: 12pt">
    <h4>Welcome to confirm your eduID account</h4>

    <div id="notice-frame">
        <div style="padding-top: 15px; margin-left: 15px;">
            Username: %(recipient_primary_mail_address)s<br/>
            Code: %(recipient_verification_code)s<br/>
            <strong>The code is valid until %(recipient_validity_period)s.</strong><br/>
        </div>
    </div>
    <div style="padding-top: 50px;">
        <strong>Instructions:</strong>
    </div>
    <ol>
        <li>Log in to https://dashboard.eduid.se with the username above and the
            password you used when you created your account.
        </li>
        <li>Open the tab "Identity".</li>
        <li>Click "BY POST" below "Swedish personal ID number".</li>
        <li>Click "PROCEED" and input the code from this letter.</li>
        <li>Click "OK".</li>
    </ol>
    <div style="padding-top: 50px;">
        If you did not request this letter from eduID then please report it to support@eduid.se.
    </div>
</div>
 
<p>Hi,</p>
<p>You recently asked to reset your password for your %(site_name)s account.</p>
<p>To change your password, click the link below:</p>
<p><a href="%(reset_password_link)s">%(reset_password_link)s</a></p>
<p>If clicking the link does not work you can copy and paste it into your browser.</p>
<p>The password reset link is valid for %(password_reset_timeout)s hours.</p>
<p>(This is an automated email. Please do not reply.)</p>
 
<p>Thank you for registering with <a href="%(site_url)s">%(site_name)s</a>.</p>

<p>To confirm that you own this email address, simply click on the following link:

<a href="%(verification_link)s">%(verification_link)s</a></p>

<p>If clicking on the link above does not work, go to your profile and emails section. Click on the
confirmation icon and enter the following code:</p>

<p><strong>%(code)s</strong></p>

 
Hi,

You are invited to join the group %(group_display_name)s with your %(site_name)s account.

To accept or decline the invitation go to %(group_invite_url)s.

If you do not have an %(site_name)s account you can create one at
%(site_url)s.

(This is an automated email. Please do not reply.)
 
Hi,

You recently asked to reset your password for your %(site_name)s account.

To change your password, click the link below:

%(reset_password_link)s

If clicking the link does not work you can copy and paste it into your browser.

The password reset link is valid for %(password_reset_timeout)s hours.

(This is an automated email. Please do not reply.)
 
Hi,

Your invite to the group %(group_display_name)s was canceled.

(This is an automated email. Please do not reply.)
 
Thank you for registering with %(site_name)s.

To confirm that you own this email address, simply click on the following link:

%(verification_link)s

If clicking on the link above does not work, go to your profile and emails section. Click on the
verification icon and enter the following code:

%(code)s

 
This is your code for %(site_name)s.

Code: %(verification_code)s
 %(site_name)s account verification <p>Please try again.</p>
          <p>There is a link (Forgot your password?) on the login page if you do not remember
              your username or password.</p> <p>Sorry, but the requested page is unavailable due to a server hiccup.</p>
          <p>Our engineers have been notified already, so please try again later.</p> <p>The login request could not be processed.</p>
          <p>Try emptying the browsers cache and re-initiate login.</p> <p>The requested resource could not be found.</p> <p>You are already logged in.</p>
          <p>If you got here by pressing 'back' in your browser,
              you can press 'forward' to return to where you came from.</p> Access denied Already logged in Bad Request Credential expired Email: FAQ Forgot your password? Group invitation Group invitation cancelled Incorrect username or password Not Found Password: Reset password Server Error Sign in Sign up Something failed, or Javascript disabled Staff Student Technicians Terminate account Too many requests User terminated Username or password incorrect Visit the eduID Login eduID confirmation email eduID dashboard eduID login eduid-signup verification email en to confirm your Security Key (on the Security tab). to confirm your identity. to register a Security Key (on the Security tab). 