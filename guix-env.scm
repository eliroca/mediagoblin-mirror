;;; GNU MediaGoblin -- federated, autonomous media hosting
;;; Copyright © 2015, 2016 David Thompson <davet@gnu.org>
;;; Copyright © 2016 Christopher Allan Webber <cwebber@dustycloud.org>
;;; Copyright © 2019, 2020, 2021 Ben Sturmfels <ben@sturm.com.au>
;;;
;;; This program is free software: you can redistribute it and/or modify
;;; it under the terms of the GNU General Public License as published by
;;; the Free Software Foundation, either version 3 of the License, or
;;; (at your option) any later version.
;;;
;;; This program is distributed in the hope that it will be useful,
;;; but WITHOUT ANY WARRANTY; without even the implied warranty of
;;; MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
;;; GNU General Public License for more details.
;;;
;;; ========================================
;;;
;;; This file is also part of GNU MediaGoblin, but we're leaving it under GPLv3
;;; for easy merge back and forth between Guix proper.
;;;
;;; ========================================
;;;
;;; This file is intended for people who want to set up MediaGoblin hacking
;;; environment using Guix to install dependencies, but run MediaGoblin from a
;;; git checkout. See https://git.sr.ht/~mediagoblin/mediagoblin-guix for
;;; details on the Guix packaging effort.
;;;
;;;
;;; With `guix environment' you can use guix as kind of a universal
;;; virtualenv, except a universal virtualenv with magical time traveling
;;; properties and also, not just for Python.
;;;
;;; Assuming you have Guix installed, you can get a MediaGoblin hacking environment with:
;;;
;;;   guix environment -l guix-env.scm --container --network --share=$HOME/.bash_history --ad-hoc which git automake autoconf python-psycopg2
;;;
;;; or, after applying the patch to upstream Guix:
;;;
;;;   ~/ws/guix/pre-inst-env guix environment --container --network --share=$HOME/.bash_history --ad-hoc which git automake autoconf python-psycopg2
;;;
;;; You'll need to run the above command every time you close your terminal or
;;; restart your system, so a handy way to save having to remember is to install
;;; "direnv" an then create a ".envrc" file in your current directory containing
;;; the following and then run "direnv allow" when prompted:
;;;
;;;   use guix -l guix-env.scm --container --network --share=$HOME/.bash_history --ad-hoc which git automake autoconf python-psycopg2
;;;
;;; First time setup only, run:
;;;
;;;   git submodule update --init
;;;   ./bootstrap.sh
;;;   ./configure --without-virtualenv
;;;   make
;;;
;;; The devtools/update_extlib.sh script won't run on Guix due to missing
;;; "/usr/bin/env", so again for first time setup only, run:
;;;
;;;   node node_modules/.bin/bower install
;;;   ./devtools/update_extlib.sh
;;;
;;; For first time setup only with a regular `guix environment` or an
;;; `environment --pure`, but required EACH TIME you start an `environment
;;; --container` (because the generated profile goes away, breaking the links in
;;; the virtualenv):
;;;
;;;   rm -rf bin include lib lib64 pyvenv.cfg
;;;   python3 -m venv --system-site-packages . && bin/python setup.py develop --no-deps
;;;
;;; ... wait whaaat, what's that venv line?!  I thought you said this
;;; was a reasonable virtualenv replacement!  Well it is and it will
;;; be, but there's a catch, and the catch is that Guix doesn't know
;;; about this directory and "setup.py dist" is technically necessary
;;; for certain things to run, so we have a virtualenv with nothing
;;; in it but this project itself.
;;;
;;; For first time setup only, migrate the database and add a user:
;;;
;;;   bin/gmg --conf_file mediagoblin.ini dbupdate
;;;   bin/gmg --conf_file mediagoblin.ini adduser --username admin --password a --email admin@example.com
;;;
;;; This can also work:
;;;
;;;   alias gmg="PYTHONPATH=.:$PYTHONPATH python3 mediagoblin/gmg_commands/__init__.py"
;;;   gmg --conf_file mediagoblin.ini dbupdate
;;;   gmg --conf_file mediagoblin.ini adduser --username admin --password a --email admin@example.com
;;;
;;; Start the server. The ./lazyserver.sh script doesn't currently work. The
;;; PYTHONPATH business is required to prefer the virtualenv packages over the
;;; `guix environment` ones.:
;;;
;;;   CELERY_ALWAYS_EAGER=true paster serve paste.ini --reload
;;;
;;; To run with a separate Celery, ensure that you have Redis installed as a
;;; system service (outside of your environment). Then in your mediagoblin.ini, set:
;;;
;;;   [celery]
;;;   BROKER_URL = "redis://"
;;;
;;; Then start Celery:
;;;
;;;   MEDIAGOBLIN_CONFIG=mediagoblin.ini CELERY_CONFIG_MODULE=mediagoblin.init.celery.from_celery bin/python -m celery worker --loglevel=INFO
;;;
;;; Start a separate environment and run:
;;;
;;;   CELERY_ALWAYS_EAGER=false paster serve paste.ini --reload
;;;
;;;
;;; Run the tests:
;;;
;;;   bin/python -m pytest -rs ./mediagoblin/tests/ --boxed
;;;
;;; or:
;;;
;;;   PYTHONPATH="${PYTHONPATH}:$(pwd)" ./runtests.sh
;;;
;;;
;;; Now notably this is goofier looking than running a virtualenv,
;;; but soon I'll do something truly evil (I hope) that will make
;;; the virtualenv and path-hacking stuff unnecessary.
;;;
;;; Have fun!

(use-modules (ice-9 match)
             (srfi srfi-1)
             (guix packages)
             ((guix licenses) #:prefix license:)
             (guix download)
             (guix git-download)
             (guix build-system gnu)
             (guix build-system python)
             (gnu packages)
             (gnu packages audio)
             (gnu packages autotools)
             (gnu packages base)
             (gnu packages certs)
             (gnu packages check)
             (gnu packages databases)
             (gnu packages openldap)
             (gnu packages pdf)
             (gnu packages python)
             (gnu packages python-crypto)
             (gnu packages python-web)
             (gnu packages python-xyz)
             (gnu packages sphinx)
             (gnu packages gstreamer)
             (gnu packages glib)
             (gnu packages pulseaudio)
             (gnu packages rsync)
             (gnu packages ssh)
             (gnu packages time)
             (gnu packages video)
             (gnu packages version-control)
             (gnu packages xml))

(define mediagoblin
  (package
    (name "mediagoblin")
    (version "0.12.0.dev.1")
    (source
     (origin
       (method git-fetch)
       (uri (git-reference
             (url "https://git.savannah.gnu.org/git/mediagoblin.git")
             (commit "f620b65e050e00ebdf7a6f9e07a835a3b285954c")))
       (file-name (git-file-name name version))
       (sha256
        (base32 "1gmmxa8yggb8pcsff66b8d45jsqkal01kkb9nqn5h036mx412g9k"))))
    (build-system python-build-system)
    (arguments
     `(#:phases
       (modify-phases %standard-phases
         (add-after 'build 'build-translations
           (lambda _
             (invoke "devtools/compile_translations.sh")))
         (replace 'check
           (lambda _
             (setenv "PYTHONPATH"
                     (string-append (getcwd) ":"
                                    (getenv "PYTHONPATH")))
             (invoke "pytest" "mediagoblin/tests" "-rs" "--boxed"
                     ;; Skip the audio tests until updated libsndfile
                     ;; has been merged from core-updates branch.
                     "--deselect=test_audio.py::test_thumbnails"
                     "--deselect=test_submission.py::TestSubmissionAudio"))))))
    (native-inputs
     `(("python-pytest" ,python-pytest)
       ("python-pytest-forked" ,python-pytest-forked)
       ("python-pytest-xdist" ,python-pytest-xdist)
       ("python-sphinx" ,python-sphinx)
       ("python-webtest" ,python-webtest)))
    (inputs
     `(("python-alembic" ,python-alembic)
       ("python-babel" ,python-babel)
       ("python-celery" ,python-celery)
       ("python-configobj" ,python-configobj)
       ("python-dateutil" ,python-dateutil)
       ("python-email-validator" ,python-email-validator)
       ("python-exif-read" ,python-exif-read)
       ("python-feedgenerator" ,python-feedgenerator)
       ("python-itsdangerous" ,python-itsdangerous)
       ("python-jinja2" ,python-jinja2)
       ("python-jsonschema" ,python-jsonschema)
       ("python-ldap" ,python-ldap)  ; For LDAP plugin
       ("python-lxml" ,python-lxml)
       ("python-markdown" ,python-markdown)
       ("python-oauthlib" ,python-oauthlib)
       ("python-openid" ,python-openid) ; For OpenID plugin
       ("python-pastescript" ,python-pastescript)
       ("python-pillow" ,python-pillow)
       ("python-bcrypt" ,python-bcrypt)
       ("python-pyld" ,python-pyld)
       ("python-pytz" ,python-pytz)
       ("python-requests" ,python-requests) ; For batchaddmedia
       ("python-soundfile" ,python-soundfile)
       ("python-sqlalchemy" ,python-sqlalchemy)
       ("python-unidecode" ,python-unidecode)
       ("python-waitress" ,python-waitress)
       ("python-werkzeug" ,python-werkzeug)
       ("python-wtforms" ,python-wtforms)

       ;; Audio/video media
       ;; TODO: MP4 failing since moving from propagated-inputs to inputs.
       ("gobject-introspection" ,gobject-introspection)
       ("gst-libav" ,gst-libav)
       ("gst-plugins-bad" ,gst-plugins-bad)
       ("gst-plugins-base" ,gst-plugins-base)
       ("gst-plugins-good" ,gst-plugins-good)
       ("gst-plugins-ugly" ,gst-plugins-ugly)
       ("gstreamer" ,gstreamer)
       ("openh264" ,openh264)
       ("python-gst" ,python-gst)  ; For tests to pass
       ("python-numpy" ,python-numpy)  ; Audio spectrograms
       ("python-pygobject" ,python-pygobject)

       ;; PDF media.
       ;;
       ;; jgart suggests that we'll need to wrap the binaries used in
       ;; mediagoblin/media_types/pdf/processing.py - pdftocairo, pdfinfo, and
       ;; unoconv probably need to be wrapped to point to the executable that is
       ;; in /gnu/store. See this issue for a similar discussion about wrapping
       ;; binaries with guix: https://issues.guix.gnu.org/50833
       ("poppler" ,poppler)))
    (home-page "https://mediagoblin.org/")
    (synopsis "Web application for media publishing")
    (description
     "MediaGoblin is a free software media publishing platform that anyone can
run. You can think of it as a decentralized alternative to Flickr, YouTube,
SoundCloud, etc.")
    (license (list license:agpl3+ license:cc0))))

mediagoblin
