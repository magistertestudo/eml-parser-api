"""Local, interactive OAuth bootstrap; credentials never enter command arguments."""
import argparse
import getpass
import os
from pathlib import Path
import sys

import httpx
from pcloud_client import PCloudClient, PCloudError, Settings

CLIENT_ID = 'Nza57ibxa3Y'
HOST = 'api.pcloud.com'  # Region of the verified destination folder.
PARENT_ID = 29662386698


def exchange(code, secret, transport=None):
    with httpx.Client(base_url='https://' + HOST, timeout=30,
                      follow_redirects=False, transport=transport) as client:
        try:
            response = client.post('/oauth2_token', data={
                'client_id': CLIENT_ID, 'client_secret': secret, 'code': code,
            })
            response.raise_for_status()
            data = response.json()
        except (httpx.HTTPError, ValueError):
            raise PCloudError('Scambio OAuth interrotto: errore di rete o risposta non valida.') from None
    if not isinstance(data, dict) or data.get('result') != 0:
        result = data.get('result') if isinstance(data, dict) else None
        result = result if type(result) is int else 'non disponibile'
        raise PCloudError(f'Scambio OAuth non completato (codice {result}). Nessun token salvato.')
    token = data.get('access_token')
    if not isinstance(token, str) or not token or any(c.isspace() for c in token):
        raise PCloudError('Token OAuth non valido nella risposta.')
    return token


def save_token(path, token):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, 'w') as output:
        output.write('PCLOUD_AUTH_TYPE=oauth\nPCLOUD_ACCESS_TOKEN=' + token + '\n')
        output.write('PCLOUD_API_HOST=' + HOST + '\nPCLOUD_PARENT_FOLDER_ID=' + str(PARENT_ID) + '\n')


def main():
    arguments = argparse.ArgumentParser(description=__doc__)
    arguments.add_argument('--manageshares', action='store_true',
                           help='Salva separatamente il token e verifica le richieste file.')
    options = arguments.parse_args()
    target = Path(__file__).with_name('.env.pcloud.oauth.manageshares.secret'
                                    if options.manageshares else '.env.pcloud.oauth.secret')
    if target.exists():
        raise PCloudError('Token OAuth locale già presente. Non ripetere: torna alla conversazione per verificarlo.')
    if not sys.stdin.isatty():
        raise PCloudError('Aprire un Terminale interattivo per inserire i dati nascosti.')
    print('Autorizzazione OAuth pCloud. I dati incollati resteranno invisibili.')
    secret = getpass.getpass('Client Secret da My Apps: ').strip()
    code = getpass.getpass('Codice di autorizzazione visualizzato da pCloud: ').strip()
    if not secret or not code:
        raise PCloudError('Dati mancanti. Nessuna richiesta inviata.')
    try:
        token = exchange(code, secret)
    finally:
        secret = code = None
    # Preserve an issued token before attempting the read-only folder check.
    save_token(target, token)
    print('Token salvato localmente con permessi riservati; verifica cartella in corso.')
    with PCloudClient(Settings(token, HOST, PARENT_ID, 'oauth')) as cloud:
        meta = cloud.call('listfolder', {'folderid': PARENT_ID,
                          'filtermeta': 'folderid,isfolder,ismine'}).get('metadata', {})
        if meta.get('folderid') != PARENT_ID or not meta.get('isfolder') or not meta.get('ismine'):
            raise PCloudError('Token salvato, ma accesso alla destinazione non confermato. Non ripetere il login.')
        if options.manageshares:
            try:
                cloud.call('listuploadlinks', {})
            except PCloudError:
                raise PCloudError('Nuovo token salvato separatamente, ma verifica richieste file non riuscita. Non ripetere il login: torna alla conversazione.') from None
            print('ELENCO RICHIESTE FILE ACCESSIBILE. La creazione del link resta da collaudare.')
    print('ACCESSO OAUTH VERIFICATO. Nessun file caricato. Torna alla conversazione e scrivi: fatto.')


if __name__ == '__main__':
    try:
        main()
    except PCloudError as exc:
        print(str(exc))
        sys.exit(1)
    except OSError:
        print('Errore locale di salvataggio. Non ripetere: torna alla conversazione.')
        sys.exit(1)
    except (KeyboardInterrupt, EOFError):
        print('\nOperazione annullata.')
        sys.exit(1)
