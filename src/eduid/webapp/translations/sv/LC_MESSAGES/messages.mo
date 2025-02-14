��    ?                          �     P   �  �     �   �  �   a  �   �  �   �  �  ;	  �   �
  :  r    �  �   �  �   �    �  �  �  �  O  &  �  f    x   ~  4  �  C   ,  "   p  �   �  �   7  x   �  1   R  �   �     3     A     S     _     r     y     }     �     �     �  	   �  	   �     �                 (        G     M     U     a     s     �     �  	   �     �     �     �     �     �        3   "      V   1   p   �  �      l"  �   �#  T   X$  �   �$  �   @%  �   �%  �   �&  �   R'  �  �'  �   x)  M  *  �   i+    W,  �   ]-  ,  #.  �  P2  �  :4  8  �5  �  7  �   �8  9  C9  F   }:     �:  �   �:  �   �;  �   <     �<  �   �<     �=     �=     �=  ,   �=     �=     �=     
>     !>  !   />  '   Q>     y>  
   �>     �>  	   �>     �>     �>  2   �>  
   �>     	?     ?     ?     (?     D?  +   U?     �?     �?     �?     �?     �?     �?     �?  B   �?  !   +@  B   M@   

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
PO-Revision-Date: 2018-03-27 09:25+0000
Last-Translator: Johan Lundberg <lundberg@sunet.se>, 2022
Language: sv
Language-Team: Swedish (https://www.transifex.com/sunet/teams/84844/sv/)
Plural-Forms: nplurals=2; plural=(n != 1);
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.10.3
 

<h2>Välkommen till %(site_name)s,</h2>

<p>Du anmälde dig nyligen till <a href="%(site_url)s">%(site_name)s</a>.</p>

<p>Var vänlig bekräfta e-postadressen och få ditt lösenord genom att klicka på den här länken:</p>

<a href="%(verification_link)s">%(verification_link)s</a>

 

Välkommen till %(site_name)s,

Du anmälde dig nyligen till %(site_name)s.

Var vänlig bekräfta e-postadressen och få ditt lösenord genom att klicka på den här länken:

%(verification_link)s

 
            <p>Åtkomst kan inte ges för tillfället. Var god försök senare.</p> 
            <p>Tillgång till den önskade tjänsten kunde inte ges.
                Tjänsten begärde förmodligen en verifierad identitet.</p> 
           <p>Tillgång till den önskade tjänsten kunde inte ges.
               Tjänsten kräver att en verifierad Säkerhetsnyckel (SWAMID MFA/MFA HI) används.
            </p> 
           <p>Tillgång till den önskade tjänsten kunde inte ges.
               Tjänsten kräver att Säkerhetsnyckel (MFA) används.
            </p> 
          <p>Giltighetstiden på lösenordet har gått ut eftersom det inte har använts på 18 månader.</p>
	  <p>För att kunna logga in igen så måste lösenordet återställas.</p>
	 
            <p>Det här kontot har tagits bort.</p>
	  <p>För att få tillgång till kontot igen så måste lösenordet återställas.</p>
	 
<p>Hej,</p>
<p>Du är inbjuden att gå med i gruppen %(group_display_name)smed ditt <a href=%(site_url)s>%(site_name)s-konto</a>.
<p>För att acceptera inbjudan gå till <a href=%(group_invite_url)s>%(group_invite_url)s</a>.</p>
<p>Om du inte redan har ett %(site_name)s-konto så kan du <a href="%(site_url)s">skapa ett</a>.</p>
<p>(Detta är ett automatiserat meddelande och går ej att svara på.)</p>
 
<p>Hej,</p>
<p>Din inbjudan till gruppen %(group_display_name)s har tagits tillbaka.</p>
<p>(Det här är ett automatiskt mejl och går inte att svar på.) </p>
 
    <p>Du har valt att ta bort ditt <a href="%(site_url)s">%(site_name)s</a>-konto.</p>

    <p><strong>Om det inte var du som tog bort kontot så återställ ditt lösenord omedelbart.</strong></p>

    <p>Tack för att du använde %(site_name)s.</p>

    <p>(Detta är ett automatiserat meddelande och går ej att svara på.)</p>
 
<p>Du har försökt bekräfta ditt konto hos<a href="%(site_url)s">%(site_name)s</a>.</p>
<p>Tyvärr uppstod ett problem så vi måste be dig att bekräfta ditt konto igen med något av de andra sätten att verifiera din identitet.</p>
 
    Du har valt att ta bort ditt %(site_name)s-konto.

    Om det inte var du som tog bort kontot så återställ ditt lösenord omedelbart.

    Tack för att du använde %(site_name)s.

    (Detta är ett automatiserat meddelande och går ej att svara på.)
 
Du har försökt bekräfta ditt konto hos%(site_name)s.

Tyvärr uppstod ett problem så vi måste be dig att bekräfta ditt konto igen med något av de andra sätten att verifiera din identitet.
 
<div id="text_frame" style="font-size: 12pt">
    <h4>Välkommen att bekräfta ditt eduID-konto</h4>

    <div id="notice-frame">
        <div style="padding-top: 15px; margin-left: 15px;">
            Användarnamn: %(recipient_primary_mail_address)s<br/>
            Kod: %(recipient_verification_code)s<br/>
            <strong>Koden är giltig till och med: %(recipient_validity_period)s</strong><br/>
        </div>
    </div>
    <div style="padding-top: 50px;">
        <strong>Instruktioner:</strong>
    </div>
    <ol>
        <li>Logga in på https://dashboard.eduid.se med användarnamnet ovan och det
            lösenord som du använde när du skapade ditt konto.
        </li>
        <li>Öppna fliken "Identitet".</li>
        <li>Klicka på rutan "VIA POST" under "Svenskt personnummer".</li>
        <li>Skriv in koden från det här brevet.</li>
        <li>Klicka på "OK".</li>
    </ol>
    <div style="padding-top: 50px;">
        Om du inte har begärt en kod från eduID vänligen rapportera detta till support@eduid.se.
    </div>
</div>
 
<p>Hej,</p>
<p>Du har bett om att byta lösenord för ditt %(site_name)s-konto.</p>
<p>För att byta lösenord, klicka på länken nedan:</p>
<p><a href="%(reset_password_link)s">%(reset_password_link)s</a></p>
<p>Om det inte går att klicka på länken kan du kopiera och klistra in den i din webbläsare.</p>
<p>Länken för återställning av ditt lösenord är giltig i %(password_reset_timeout)s timmar.</p>
<p>(Detta är ett automatiserat meddelande och går ej att svara på.)</p>
 
<p>Tack för att du registrerade dig hos <a href="%(site_url)s">%(site_name)s</a>.</p>

<p>Lättaste sättet att bekräfta din mejladress är att klicka på länken nedan:

<a href="%(verification_link)s">%(verification_link)s</a></p>

<p>Fungerar inte länken så kan du logga in på din profil, gå till e-post-fliken och klicka på bekräfta. Klistra sedan in nedanstående kod:</p>

<p><strong>%(code)s</strong></p>

 
Hej,

Du är inbjuden att gå med i gruppen %(group_display_name)s med ditt %(site_name)s-konto.

För att acceptera inbjudan gå till %(group_invite_url)s.

Om du inte redan har ett %(site_name)s-konto så kan du skapa ett på %(site_url)s.

(Detta är ett automatiserat meddelande och går ej att svara på.)
 
Hej,

Du har bett om att byta lösenord för ditt %(site_name)s-konto.

För att byta lösenord, klicka på länken nedan:

%(reset_password_link)s

Om det inte går att klicka på länken kan du kopiera och klistra in den i din webbläsare.

Länken för återställning av ditt lösenord är giltig i %(password_reset_timeout)s timmar.

(Detta är ett automatiserat meddelande och går ej att svara på.)
 
Hej,

Din inbjudan till gruppen %(group_display_name)s har tagits tillbaka.

(Det här är ett automatiskt mejl och går inte att svar på.) 
 
Tack för att du registrerade dig hos%(site_name)s.

Lättaste sättet att bekräfta din mejladress är att klicka på länken nedan:

%(verification_link)s

Fungerar inte länken så kan du logga in på din profil, gå till e-post-fliken och klicka på bekräfta. Klistra sedan in nedanstående kod:

%(code)s

 
Det här är din kod för %(site_name)s.

Kod: %(verification_code)s
 %(site_name)skontobekräftning <p>Var god försök igen.</p>
          <p>Det finns en länk (Glömt ditt lösenord?) på inloggningssidan om du inte kommer ihåg
 ditt användarnamn eller lösenord.</p> <p>Hoppsan, sidan kan inte visas på grund av ett serverfel.</p>
          <p>Våra tekniker har meddelats, så försök igen senare.</p> <p>Inloggningsförsöket misslyckades.</p>
          <p>Börja med att tömma webbläsarens cache och försök sedan logga in igen.</p> <p>Sidan kunde inte hittas</p> <p>Du är redan inloggad.</p>
           <p>Om du kom hit genom att använda 'Tillbaka'-knappen i din webbläsare
               så kan du klicka på 'Framåt'-knappen för att komma tillbaka dit du var.</p> Åtkomst nekad Redan inloggad Felaktig förfrågan Giltighetstiden på lösenordet har gått ut E-post: Vanliga frågor Glömt ditt lösenord? Gruppinbjudan Gruppinbjudan har tagits tillbaka Felaktigt användarnamn eller lösenord Kunde inte hittas Lösenord: Återställ lösenord Serverfel Logga in Skapa konto Något gick fel eller så är Javascript avstängt Anställda Student Tekniker Avsluta konto För många förfrågningar Kontot borttaget Användarnamn eller lösenord är felaktigt Besök eduID-inloggning eduID bekräftelsemejl eduID dashboard eduID-inloggning eduID registrering one för att verifiera din Säkerhetsnyckel (under Säkerhets-tabben). för att verifiera din identitet. för att registrera en Säkerhetsnyckel (under Säkerhets-tabben). 