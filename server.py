import http.server
import socketserver
import http.client
import json
import sys

# -- IP and the port of the server
IP = "localhost"  # Localhost means "I": your local machine
PORT = 8000
socketserver.TCPServer.allow_reuse_adress = True


class GeniusHandler(http.server.BaseHTTPRequestHandler):
    api_token = None

    def send_query(self, query):

        headers = {"Authorization": "Bearer " + self.api_token}

        conn = http.client.HTTPSConnection("api.genius.com")
        conn.request("GET", query, None, headers)
        r1 = conn.getresponse()
        print(r1.status, r1.reason)
        res_raw = r1.read().decode("utf-8")
        conn.close()

        repos = json.loads(res_raw)
        return repos

    def fetch_songs(self, artista):

        songs = []
        url = "/search?q=" + artista
        res_json = self.send_query(url)

        for elem in res_json['response']['hits']:
            id = elem['result']['primary_artist']['id']
            break

        if not artista:
            print("no artista parameter entered")
            return songs # in case no artista parameter has been entred by client
        try:
            url = "/artists/%s/songs?per_page=50&page=1" % (id)
        except UnboundLocalError:
            print("unrecognised artista parameter")
            return songs

        songs_res = self.send_query(url)

        songs = songs_res['response']['songs']

        print("songs for", artista, "with code", id)

        return songs

    def html_builder(self, songs, artista): # I have to thank pabloblascof for this:

        html_file = '<html><body style="background-color: yellow"><h1>Here you have some songs that match with %s:</h1>' % artista
        for song in songs:
            html_file += "<li>"
            if 'default_cover' not in song['header_image_thumbnail_url']:
                html_file += "<img align='left' height='50' width='50' src='" + song['header_image_thumbnail_url'] + "'>"
            html_file += "<a href='" + song['url'] + "'>"
            html_file += "<h4>" + song['title'] + "<h4>" + "</a></li>" # dont forget adding <h4> or html list will look odd
        html_file += "</body></html>"
        html_file += "<marquee>powered by Lasonata</marquee>"

        print("html file has been built")
        return html_file

    # GET
    def do_GET(self):

        self.send_response(200)
        self.send_header('Content-type', 'text/html')
        self.end_headers()

        path = self.path

        if path == "/":
            # default
            print("SEARCH: client entered default search web")
            with open("search.html") as f:
                message = f.read()
                self.wfile.write(bytes(message, "utf8"))
                print("file sent")

        elif 'searchSongs' in path:
            artista = path.split("=")[1]
            songs = self.fetch_songs(artista)
            if songs:
                message = self.html_builder(songs, artista)
                print("songs sent")
            else:
                message = "<h1>404 error<h1>"
                print("error message sent")


            self.wfile.write(bytes(message, "utf8"))
            self.send_response(404)

        return


GeniusHandler.api_token = sys.argv[1]

httpd = socketserver.TCPServer(("", PORT), GeniusHandler)
print("serving at %s:%s" % (IP, PORT))
try:
    httpd.serve_forever()
except KeyboardInterrupt:
    pass
httpd.server_close()
print("")
print("Server stopped!")