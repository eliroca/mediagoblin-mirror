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
;;; Progress from the Guix side is being tracked in the following "meta" bug:
;;;
;;; Package GNU MediaGoblin as a Guix service:
;;; https://debbugs.gnu.org/cgi/bugreport.cgi?bug=47260
;;;
;;; ========================================
;;;
;;; WORK IN PROGRESS - JOBS TO DO:
;;;
;;; 1. Submit the below python-soundfile package to Guix after libsndfile
;;; updates in Guix core-updates branch have been merged into master [bug
;;; 47181] https://debbugs.gnu.org/cgi/bugreport.cgi?bug=47181
;;;
;;; 2. Refine and submit the below upgraded python-wtforms 2.3.3 to Guix.
;;;
;;; 3. Don't have NPM in this environment yet. Possibly rewrite MediaGoblin's
;;; JavaScript code not to use jQuery. Possibly improve the
;;; no-bundled-JavaScript video/audio playing experience.
;;;
;;; 4. Package MediaGoblin itself as a Guix service. Look at adding a PostgreSQL
;;; database instead of sqlite3.
;;;
;;; ========================================
;;;
;;; With `guix environment' you can use guix as kind of a universal
;;; virtualenv, except a universal virtualenv with magical time traveling
;;; properties and also, not just for Python.
;;;
;;; Assuming you have Guix installed, run:
;;;
;;;   guix environment -l guix-env.scm --container --network --share=$HOME/.bash_history
;;;
;;; or, after applying the patch to upstream Guix:
;;;
;;;   ~/ws/guix/pre-inst-env guix environment --container --network --share=$HOME/.bash_history --ad-hoc mediagoblin python
;;;
;;; You'll need to run the above command every time you close your terminal or
;;; restart your system, so a handy way to save having to remember is to install
;;; "direnv" an then create a ".envrc" file in your current directory containing
;;; the following and then run "direnv allow" when prompted:
;;;
;;;   use guix -l guix-env.scm
;;;
;;; First time setup only, run:
;;;
;;;   git submodule update --init
;;;   ./bootstrap.sh
;;;   ./configure --without-virtualenv
;;;   make
;;
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
             (guix licenses)
             (guix download)
             (guix git-download)
             (guix build-system gnu)
             (guix build-system python)
             (gnu packages)
             (gnu packages xiph)  ; flac for embedded libsndfile
             (gnu packages autotools)
             (gnu packages base)
             (gnu packages certs)
             (gnu packages check)
             (gnu packages compression)  ; unzip for embedded python-wtforms
             (gnu packages databases)
             (gnu packages libffi)  ; cffi for embedded python-soundfile
             (gnu packages openldap)
             (gnu packages pdf)
             (gnu packages pkg-config)  ; embedded libsndfile
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
             (gnu packages xml)
             ((guix licenses) #:select (bsd-3 gpl2+) #:prefix license:))

;; =================================================================
;; These packages are on their way into Guix proper but haven't made
;; it in yet... or they're old versions of packages we're pinning
;; ourselves to...
;; =================================================================

;; Upgraded the Guix version 2.1 to 2.3 for compatibility with current
;; MediaGoblin.
(define python-wtforms
  (package
    (name "python-wtforms")
    (version "2.3.3")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "WTForms" version))
       (sha256
        (base32
         ;; Interesting, if this has is that of a lower version, it blindly
         ;; ignores the version number above and you silently get the older
         ;; version.
         "17427m7p9nn9byzva697dkykykwcp2br3bxvi8vciywlmkh5s6c1"))))
    (build-system python-build-system)
    (arguments
     `(#:tests? #f))  ; TODO: Fix tests for upgraded version.
    (propagated-inputs
    `(("python-markupsafe" ,python-markupsafe)))
    (native-inputs
     `(("unzip" ,unzip)))  ; CHECK WHETHER NEEDED - not in `guix import` but is in old package.
    (home-page "http://wtforms.simplecodes.com/")
    (synopsis
     "Form validation and rendering library for Python web development")
    (description
     "WTForms is a flexible forms validation and rendering library
for Python web development.  It is very similar to the web form API
available in Django, but is a standalone package.")
    (license license:bsd-3)))


;; Copied from guix/gnu/packages/pulseaudio.scm in the core-updates branch which
;; adds flac/ogg/vorbis/opus support. This is required for building
;; python-soundfile (March 2021).
(define libsndfile
  (package
    (name "libsndfile")
    (version "1.0.30")
    (source (origin
             (method url-fetch)
             (uri (string-append "https://github.com/erikd/libsndfile"
                                 "/releases/download/v" version
                                 "/libsndfile-" version ".tar.bz2"))
             (sha256
              (base32
               "06k1wj3lwm7vf21s8yqy51k6nrkn9z610bj1gxb618ag5hq77wlx"))
             (modules '((ice-9 textual-ports) (guix build utils)))
             (snippet
              '(begin
                 ;; Remove carriage returns (CRLF) to prevent bogus
                 ;; errors from bash like "$'\r': command not found".
                 (let ((data (call-with-input-file
                                 "tests/pedantic-header-test.sh.in"
                               (lambda (port)
                                 (string-join
                                  (string-split (get-string-all port)
                                                #\return))))))
                   (call-with-output-file "tests/pedantic-header-test.sh.in"
                     (lambda (port) (format port data))))

                 ;; While at it, fix hard coded executable name.
                 (substitute* "tests/test_wrapper.sh.in"
                   (("^/usr/bin/env") "env"))
                 #t))))
    (build-system gnu-build-system)
    (propagated-inputs
     `(("flac" ,flac)
       ("libogg" ,libogg)
       ("libvorbis" ,libvorbis)
       ("opus" ,opus)))
    (native-inputs
     `(("pkg-config" ,pkg-config)
       ("python" ,python)))
    (home-page "http://www.mega-nerd.com/libsndfile/")
    (synopsis "Reading and writing files containing sampled sound")
    (description
     "Libsndfile is a C library for reading and writing files containing
sampled sound (such as MS Windows WAV and the Apple/SGI AIFF format) through
one standard library interface.

It was designed to handle both little-endian (such as WAV) and
big-endian (such as AIFF) data, and to compile and run correctly on
little-endian (such as Intel and DEC/Compaq Alpha) processor systems as well
as big-endian processor systems such as Motorola 68k, Power PC, MIPS and
SPARC.  Hopefully the design of the library will also make it easy to extend
for reading and writing new sound file formats.")
    (license license:gpl2+)))

;; Need soundfile for new Python 3 audio spectrograms. Can me merged into Guix
;; once core-updates is merged.
(define python-soundfile
  (package
    (name "python-soundfile")
    (version "0.10.3.post1")
    (source
     (origin
       (method url-fetch)
       (uri (pypi-uri "SoundFile" version))
       (sha256
        (base32
         "0yqhrfz7xkvqrwdxdx2ydy4h467sk7z3gf984y1x2cq7cm1gy329"))))
    (build-system python-build-system)
    (native-inputs
     `(("python-pytest" ,python-pytest)))
    (propagated-inputs
     `(("python-cffi" ,python-cffi)
       ("libsndfile" ,libsndfile)
       ("python-numpy" ,python-numpy)))
    (arguments
     `(#:phases
       (modify-phases %standard-phases
         (add-before 'build 'set-library-file-name
           (lambda* (#:key inputs #:allow-other-keys)
             (let ((libsndfile (assoc-ref inputs "libsndfile")))
               (substitute* "soundfile.py"
                 (("_find_library\\('sndfile'\\)")
                  (string-append "'" libsndfile "/lib/libsndfile.so.1'")))
               #t))))))
    (home-page "https://github.com/bastibe/python-soundfile")
    (synopsis "An audio library based on libsndfile, CFFI and NumPy")
    (description
     "The soundfile module can read and write sound files, representing audio
data as NumPy arrays.")
    (license license:bsd-3)))

;; =================================================================

(define mediagoblin
  (package
    (name "mediagoblin")
    (version "0.12.0.dev")
    (source
     (origin
       (method git-fetch)
       (uri (git-reference
             (url "https://git.savannah.gnu.org/git/mediagoblin.git")
             (commit "39effee4f0b8e75d8107d59f3a1d1a4b525e6fd5")))
       (file-name (git-file-name name version))
       (sha256
        (base32 "0v5xdaf6jz4q6vdkiss4z41iyx8a8rvhlq7gy6ghvppklb2msdap"))))
    (build-system python-build-system)
    (arguments
     `(
       ;; #:tests? #f
       #:phases (modify-phases %standard-phases
                  (replace 'check
                    (lambda _
                      (setenv "PYTHONPATH"
                              (string-append (getcwd) ":"
                                             (getenv "PYTHONPATH")))
                      ;; Translations needed for tests to pass. Probably
                      ;; should be done during build stage?
                      (invoke "./devtools/compile_translations.sh")
                      (invoke "pytest" "./mediagoblin/tests" "-rs" "--boxed")
                      #t)))
                ))
    (native-inputs
     `(("nss-certs" ,nss-certs)
       ("python-pytest" ,python-pytest)
       ("python-pytest-forked" ,python-pytest-forked)
       ("python-pytest-xdist" ,python-pytest-xdist)
       ("python-webtest" ,python-webtest)))
    ;; lle-bout suggests avoiding propagated-inputs and insteading creating
    ;; wrappers scripts. See:
    ;; https://debbugs.gnu.org/cgi/bugreport.cgi?bug=47260#44
    (propagated-inputs
     `(("python-alembic" ,python-alembic)
       ("python-babel" ,python-babel)
       ("python-celery" ,python-celery)
       ("python-configobj" ,python-configobj)
       ("python-dateutil" ,python-dateutil)
       ("python-docutils" ,python-docutils)  ; What for?
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
       ("python-openid" ,python-openid)  ; For OpenID plugin
       ("python-pastescript" ,python-pastescript)
       ("python-pillow" ,python-pillow)
       ("python-py-bcrypt" ,python-py-bcrypt)
       ("python-pyld" ,python-pyld)
       ("python-pytz" ,python-pytz)
       ("python-requests" ,python-requests)  ; For Persona plugin, batchaddmedia
       ("python-setuptools" ,python-setuptools)  ; What for?
       ("python-soundfile" ,python-soundfile)
       ("python-sphinx" ,python-sphinx)
       ("python-sqlalchemy" ,python-sqlalchemy)
       ("python-unidecode" ,python-unidecode)
       ("python-waitress" ,python-waitress)
       ("python-werkzeug" ,python-werkzeug)
       ("python-wtforms" ,python-wtforms)

       ;; Audio/video media
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
       ("poppler" ,poppler)

       ))
    (home-page "https://mediagoblin.org/")
    (synopsis "Web application for media publishing")
    (description "MediaGoblin is a web application for publishing all kinds of
media.")
    (license agpl3+)))

(package
  (inherit mediagoblin)
  (name "mediagoblin-hackenv")
  (version "git")
  (inputs
   `(("mediagoblin" ,mediagoblin)
     ("which" ,which)
     ("git" ,git)
     ("automake" ,automake)
     ("autoconf" ,autoconf)))
  (propagated-inputs
   `(("python-virtualenv" ,python-virtualenv)
     ("python-chardet", python-chardet)
     ("python-psycopg2" ,python-psycopg2)
     ("openssh" ,openssh)
     ("rsync" ,rsync))))
