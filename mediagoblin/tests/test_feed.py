from mediagoblin.tests.tools import fixture_add_user, fixture_media_entry


class TestFeeds:
    def setup(self):
        self.user = fixture_add_user(username='terence', privileges=['active'])
        self.media_entry = fixture_media_entry(
            uploader=self.user.id,
            state='processed')

    def test_site_feed(self, test_app):
        res = test_app.get('/atom/')
        assert res.status_int == 200
        assert res.content_type == 'application/atom+xml'

    def test_user_feed(self, test_app):
        res = test_app.get('/u/terence/atom/')
        assert res.status_int == 200
        assert res.content_type == 'application/atom+xml'
