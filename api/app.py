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



if __name__ == '__main__':
    # define the localhost ip and the port that is going to be used
    app.run(host='0.0.0.0', port=5000)
