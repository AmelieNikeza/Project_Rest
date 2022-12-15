from flask import Flask, jsonify, abort, request
import mariadb
import urllib.parse

app = Flask(__name__)

app.config['JSON_AS_ASCII'] = False  # pour utiliser l'UTF-8 plutot que l'unicode


def execute_query(query, data=()):
    config = {
        'host': 'mariadb',
        'port': 3306,
        'user': 'root',
        'password': 'root',
        'database': 'mydatabase'
    }
    """Execute une requete SQL avec les param associés"""
    # connection for MariaDB
    conn = mariadb.connect(**config)
    # create a connection cursor
    cur = conn.cursor()
    # execute a SQL statement
    cur.execute(query, data)

    if cur.description:
        # serialize results into JSON
        row_headers = [x[0] for x in cur.description]
        rv = cur.fetchall()
        list_result = []
        for result in rv:
            list_result.append(dict(zip(row_headers, result)))
        return list_result
    else:
        conn.commit()
        return cur.lastrowid

# we define the route /
@app.route('/')
def welcome():
    liens = [{}]
    liens[0]["_links"] = [{
        "href": "/utilisateurs",
        "rel": "utilisateurs"
    }, {
        "href": "/groupes",
        "rel": "groupes"
    },{
        "href": "/concerts",
        "rel": "concerts"
    },{
        "href": "/billets",
        "rel": "billets"
    }
    ]
    return jsonify(liens), 200

""" ################## UTILISATEURS ##################
    #############################################"""


@app.route('/utilisateurs')
def get_utilisateurs():
    """recupère la liste des utilisateurs"""
    utilisateurs = execute_query("select nom from utilisateurs")

    for i in range(len(utilisateurs)):
        utilisateurs[i]["_links"] = [
            {
                "href": "/utilisateurs/" + urllib.parse.quote(utilisateurs[i]["nom"]),
                "rel": "self"
            },
            {
                "href": "/utilisateurs/" + urllib.parse.quote(utilisateurs[i]["nom"]) + "/billets",
                "rel": "billets"
            }
        ]
    return jsonify(utilisateurs), 200

@app.route('/utilisateurs/<string:nom>')
def get_utilisateur(nom):
    """"Récupère les infos de l'utilisateur"""
    utilisateurs = execute_query("select nom from utilisateurs where nom=?", (nom,))
    # ajout de _links à l'utilisateur 
    utilisateurs[0]["_links"] = [{
        "href": "/utilisateurs/" + urllib.parse.quote(utilisateurs[0]["nom"]) + "/billets",
        "rel": "billets"
    }]
    return jsonify(utilisateurs), 200

@app.route('/utilisateurs', methods=['POST'])
def post_utilsateurs():
    """"Ajoute un utilisateur"""
    nom = request.args.get("nom")
    execute_query("insert into utilisateurs (nom) values (?)", (nom,))
    # on renvoi le lien de l'utilsateur 
    reponse_json = jsonify({
        "_links": [{
            "href": "/utilsateurs/" + urllib.parse.quote(nom),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created

@app.route('/utilisateurs/<string:nom_utilisateur>', methods=['DELETE'])
def delete_utilisateurs(nom_utilisateur):
    """supprimer un utilisateur"""
    execute_query("delete from utilisateurs where nom=?", (nom_utilisateur, ))
    return "", 204

""" ################## GROUPES ##################
    #############################################"""


@app.route('/groupes')
def get_groupes():
    """recupère la liste des groupes"""
    groupes = execute_query("select id, nom from groupes")
    # ajout de _links à chaque dico groupes
    for i in range(len(groupes)):
        groupes[i]["_links"] = [
            {
                "href": "/groupes/" + urllib.parse.quote(groupes[i]["nom"]),
                "rel": "self"
            },
            {
                "href": "/groupes/" + urllib.parse.quote(groupes[i]["nom"]) + "/concerts",
                "rel": "concerts"
            }
        ]
    return jsonify(groupes), 200
    
@app.route('/groupes', methods=['POST'])
def post_groupe():
    """Ajoute un groupe"""
    nom = request.args.get("nom")
    groupes = execute_query("INSERT INTO groupes(nom) VALUES (?)",(nom,))
    # on renvoi le lien du groupe que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/groupes/" + urllib.parse.quote(nom),
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created



@app.route('/groupes/<string:nom>', methods=['DELETE'])
def delete_groupe(nom):
    """Supprimer un groupe"""
    execute_query("delete from groupes where nom=?", (urllib.parse.unquote(nom), ))
    return "", 204  # no data


""" ################## BILLETS ##################
    #############################################"""
    
@app.route('/billets')
def get_billets():
    """récupère les billets"""
    billets = execute_query("select * from billets")
    for i in range(len(billets)):
        billets[i]["_links"] = [{
            "href": "/billets/" + str(billets[i]["id"]),
            "rel": "self"
        }]
    return jsonify(billets), 200

@app.route('/billets/<int:id>')
def get_billet(id):
    """Récupère les infos d'un billet en envoyant une requete HTTP
       Si le billet n'existe pas renvoi 404
    """
    billets = execute_query("select * from billets where id = ?", (id,))
    if billets == []:
        abort(404, "Ce billet n'existe pas")
    billets[0]["_links"] = [{
        "href": "/billets/" + str(billets[0]["id"]),
        "rel": "self"
    }]
    return jsonify(billets), 200

@app.route('/utilisateurs/<string:nom_utilisateur>/concerts/<string:id_concert>/billets', methods=['POST'])
def post_billet(nom_utilisateur,id_concert):
    """créé un billet"""
    prix_billet = request.args.get("prix")
    execute_query("insert into billets (concert_id, prix, utilisateur_id) values ((select id from concerts where id = ?), ?, (select id from utilisateurs where nom = ?))", (id_concert, prix_billet, nom_utilisateur))
    # on renvoi le lien du billet  que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/billets/" + prix_billet,
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created

@app.route('/billets/<id_billet>', methods=['DELETE'])
def delete_billet(id_billet):
    """supprimer un billet"""
    execute_query("delete from billets where id=?", (id_billet, ))
    return "", 204

""" ################## CONCERTS ##################
    #############################################"""

@app.route('/groupes/<string:nom>/concerts')
def get_concert_from_groupe(nom):
    """Récupère les concerts d'un groupe"""
    concerts = execute_query("""SELECT concerts.id, concerts.groupe_id, concerts.duree, concerts.date FROM concerts 
                            JOIN groupes on concerts.groupe_id = groupes.id
                            WHERE groupes.nom = ?""", (urllib.parse.unquote(nom),))
    if concerts == []:
        abort(404, "Aucuns concerts pour ce groupe")
    else:
        for i in range(len(concerts)):
            concerts[i]["_links"] = [
                {
                    "href": "/concerts/" + str(concerts[i]["id"]),
                    "rel": "self"
                },
                {
                    "href": "/concerts/" + str(concerts[i]["id"]) + "/billets",
                    "rel": "concerts"
                }
            ]
    return jsonify(concerts), 200

@app.route('/concerts')
def get_concerts():
    """récupère la liste des concerts"""
    concerts = execute_query("SELECT id, groupe_id, duree, date FROM concerts")
    # ajout de _links à chaque dico groupes
    for i in range(len(concerts)):
        concerts[i]["_links"] = [
            {
                "href": "/concerts/" + str(concerts[i]["id"]),
                "rel": "self"
            },
            {
                "href": "/concerts/" + str(concerts[i]["id"]) + "/billets",
                "rel": "concerts"
            }
        ]
    return jsonify(concerts), 200

@app.route('/groupe/<string:nom_groupe>/concerts', methods=['POST'])
def post_concert_from_groupe(nom_groupe):
    """Ajoute un concert à un groupe"""
    date = request.args.get("date")
    duree = request.args.get("duree")
    concert = execute_query("INSERT INTO concerts(date,duree,groupe_id) VALUES (?, ?, (SELECT id FROM groupes WHERE nom = ?))",(date,duree,nom_groupe))
    # on renvoi le lien du concert que l'on vient de créer
    reponse_json = jsonify({
        "_links": [{
            "href": "/groupe/" + urllib.parse.quote(nom_groupe) + "/concerts",
            "rel": "self"
        }]
    })
    return reponse_json, 201  # created

@app.route('/concerts/<string:concert_id>', methods=['DELETE'])
def delete_concert(concert_id):
    """Supprimer un concert"""
    execute_query("delete from concerts where id=?", (concert_id, ))
    return "", 204  # no data   



if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
