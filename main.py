#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import jinja2
import os
import webapp2
from google.appengine.api import users
from google.appengine.ext import blobstore
from google.appengine.ext import db
from google.appengine.ext.webapp import blobstore_handlers

template_env = jinja2.Environment( loader=jinja2.FileSystemLoader(os.getcwd()))

class UserUpload(db.Model):
    user = db.UserProperty()
    description = db.StringProperty()
    blob = blobstore.BlobReferenceProperty()

class MainPage(webapp2.RequestHandler):
    def get(self):
        user = users.get_current_user()
        login_url = users.create_login_url(self.request.path)
        logout_url = users.create_logout_url(self.request.path)

        uploads = None
        if user:
            q = UserUpload.all()
            q.filter('user =', user)
            q.ancestor(db.Key.from_path('UserUploadGroup', user.email()))
            uploads = q.fetch(100)

        upload_url = blobstore.create_upload_url('/upload')

        template = template_env.get_template('home.html')
        context = {
            'user': user,
            'login_url': login_url,
            'logout_url': logout_url,
            'uploads': uploads,
            'upload_url': upload_url,
        }

        self.response.write(template.render(context))

class UploadHandler(blobstore_handlers.BlobstoreUploadHandler):
    def post(self):
        user = users.get_current_user()
        description = self.request.params['description']

        for blob_info in self.get_uploads('upload'):
            upload = UserUpload(parent=db.Key.from_path('UserUploadGroup', user.email()),
                                user=user,
                                description=description,
                                blob=blob_info.key())
            upload.put()
        self.redirect('/')

class ViewHandler(blobstore_handlers.BlobstoreDownloadHandler):
        def get(self):
            user = users.get_current_user()
            upload_key_str = self.request.params.get('key')
            upload = None
            if upload_key_str:
                upload = db.get(upload_key_str)

            if (not user or not upload or upload.user != user):
                self.error(404)
                return

            self.send_blob(upload.blob)

app = webapp2.WSGIApplication([
    ('/', MainPage),
    ('/upload', UploadHandler),
    ('/view', ViewHandler)
], debug=True)
