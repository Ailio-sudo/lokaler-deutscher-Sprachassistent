"""Befehl 4: Ungelesene E-Mails abfragen (IMAP, verschlüsselt).

Die Zugangsdaten (E-Mail, Passwort, IMAP-Adresse) stehen in user_data.py. Fehlen sie, wird nur ein Hinweistext
ausgegeben. Beim Anbieter muss IMAP aktiviert sein.
"""
import imaplib
import email
from email.header import decode_header
from user_data import E_MAIL, E_MAIL_PASSWORT, IMAP_ADRESS
#Teile von Stackoverflow mit Decodierung von Chatgpt kombiniert
# Ohne vollständige Zugangsdaten in user_data.py gibt es nur die Hinweis-Variante der Funktion (if-Zweig)
if E_MAIL == None or E_MAIL_PASSWORT == None or IMAP_ADRESS == None:
    print(r"Folge den Anweisungen in Sprachassistent-Code\user_data.py für E-Mail um diesen Befehl zu nutzen.")
    def check_emails():
        """Ersatzfunktion, wenn in user_data.py nicht alle E-Mail-Daten eingetragen sind: gibt nur einen Hinweistext zurück."""
        return r"Folge den Anweisungen in Sprachassistent-Code\user_data.py für E-Mail um diesen Befehl zu nutzen."
else:
    def check_emails():
        """Befehl 4: Liest die ungelesenen E-Mails im Posteingang.

        Rückgabe: Text mit der Anzahl neuer E-Mails und je einer Zeile «Von: ..., Betreff: ...».
        """
        # Set up the IMAP connection
        mail = imaplib.IMAP4_SSL(IMAP_ADRESS)
        mail.login(E_MAIL, E_MAIL_PASSWORT) #Hier ist Email und Passwort
        mail.select("inbox")

        # Search for all email messages in the inbox
        status, data = mail.search(None, 'UNSEEN')

        # Iterate through each email message and print its contents
        text = "Du hast " + str(len(data[0].split())) + " neue E-mails.\n"

        for num in data[0].split():
            status, data = mail.fetch(num, '(RFC822)')
            email_message = email.message_from_bytes(data[0][1])
            absender = email_message['From'].split(" <")
            decoded_parts = decode_header(email_message['Subject'])
            decoded_subject = ""
            for part, encoding in decoded_parts:
                if isinstance(part, bytes):
                    decoded_subject += part.decode(encoding or "utf-8")
                else:
                    decoded_subject += part
            text += f"Von: {absender[0]}, Betreff: {decoded_subject}\n"
        # Close the connection
        mail.close()
        mail.logout()
        return text

