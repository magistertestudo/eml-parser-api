"""Interactive local bootstrap. No password/token printed or passed on command line."""
import getpass
import os
from pathlib import Path
import sys
import httpx
from pcloud_client import PCloudClient, PCloudError, Settings

HOST = 'api.pcloud.com'
PARENT_ID = 29662386698


def acquire_token(email, password, transport=None):
    with httpx.Client(base_url='https://' + HOST, timeout=30, follow_redirects=False,
                      transport=transport) as client:
        try:
            response = client.post('/userinfo', data={
                'username': email, 'password': password, 'getauth': 1, 'logout': 1,
                'device': 'IN-SAFETY EML Parser API - Railway',
                'authexpire': 2592000, 'authinactiveexpire': 2592000,
            })
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError):
            raise PCloudError('Accesso interrotto: errore di rete o risposta non valida. Nessun segreto mostrato.') from None
    if not isinstance(data, dict) or data.get('result') != 0:
        code = data.get('result', 'non disponibile') if isinstance(data, dict) else 'non disponibile'
        raise PCloudError(f'Accesso pCloud non completato (codice {code}). Eventuali verifiche 2FA/restrizioni richiedono un passaggio aggiuntivo; non disattivare la 2FA.')
    token = data.get('auth')
    if not isinstance(token, str) or not token or '\n' in token or '\r' in token:
        raise PCloudError('pCloud non ha restituito un token auth utilizzabile.')
    return token


def verify_folder(token, transport=None):
    with PCloudClient(Settings(token, HOST, PARENT_ID, 'direct'), transport) as cloud:
        meta = cloud.call('listfolder', {'folderid': PARENT_ID, 'filtermeta':'folderid,isfolder,ismine,name'}).get('metadata', {})
        if meta.get('folderid') != PARENT_ID or not meta.get('isfolder') or not meta.get('ismine'):
            raise PCloudError('Accesso alla cartella di destinazione non confermato.')


def save_token(path, token):
    # Refuse overwrite/symlinks; token is excluded from Git and only owner-readable.
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        output.write('PCLOUD_AUTH_TYPE=direct\nPCLOUD_AUTH_TOKEN=' + token + '\n')
        output.write('PCLOUD_API_HOST=' + HOST + '\nPCLOUD_PARENT_FOLDER_ID=' + str(PARENT_ID) + '\n')


def main():
    target = Path(__file__).with_name('.env.pcloud.secret')
    if target.exists():
        print('È già presente un token locale. Verificarlo prima di crearne un altro.')
        return 1
    if not sys.stdin.isatty():
        print('Eseguire in un terminale interattivo: la password non deve comparire nei log.')
        return 1
    print('Accesso diretto pCloud: password inviata solo a api.pcloud.com tramite HTTPS.')
    print('Verrà richiesto un token di 30 giorni, salvato localmente con permessi riservati.')
    print('La password non viene salvata. Nessun file verrà caricato su pCloud.')
    email = input('Email pCloud [info@in-safety.it]: ').strip() or 'info@in-safety.it'
    password = getpass.getpass('Password pCloud (caratteri invisibili): ')
    try:
        token = acquire_token(email, password)
    finally:
        password = None
    # Save before verification so a issued token is available for revocation if verification fails.
    save_token(target, token)
    verify_folder(token)
    print('ACCESSO VERIFICATO. Token salvato in .env.pcloud.secret, escluso da Git.')
    print('Cartella IN-SAFETY-2026 accessibile. Torna alla conversazione e scrivi: fatto.')
    return 0


if __name__ == '__main__':
    try:
        sys.exit(main())
    except PCloudError as exc:
        print(str(exc))
        print('Se il token è già salvato, non ripetere il login; torna alla conversazione per verificarlo.')
        sys.exit(1)
    except OSError:
        print('Errore nel salvataggio locale; torna alla conversazione senza ripetere il login.')
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print('\nAccesso annullato.')
        sys.exit(1)
