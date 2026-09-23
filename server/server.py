import socket, json, copy
import numpy as np
from tps import tp1, fourier

PORT = 5000
TPS = {"tp1": tp1, "fourier": fourier}

def servir(conn):
    tampon = b""
    while True:
        data = conn.recv(65536)
        if not data:
            raise ConnectionError
        tampon += data
        while b"\n" in tampon:
            ligne, tampon = tampon.split(b"\n", 1)
            requete = json.loads(ligne)
            module = TPS[requete["tp"]]
            params = copy.deepcopy(module.DEFAUT)
            params.update(requete.get("params", {}))
            reponse = module.calculer(params)
            reponse["tp"] = requete["tp"]
            conn.sendall((json.dumps(reponse) + "\n").encode())

serveur = socket.socket()
serveur.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
serveur.bind(("0.0.0.0", PORT))
serveur.listen(1)
while True:
    print("En attente du PC...")
    conn, adresse = serveur.accept()
    print("PC connecté :", adresse)
    try:
        servir(conn)
    except (ConnectionError, OSError, ValueError) as e:
        print("Déconnexion :", e)
    conn.close()
