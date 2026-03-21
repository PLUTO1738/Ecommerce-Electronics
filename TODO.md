# TODO: Fix contact_view and chatbot to link and reply at support.html seamlessly

## Steps to complete:
1. ✅ Remove unused `chatbot` view from eshop/views.py and its URL from eshop/urls.py
2. ✅ Update support.html JS fetch URL from `/chatbot/` to `/contact/`
3. ✅ Enhance contact.html to prominently link/redirect to support.html for live chat
4. [ ] Test functionality: /support/ chat replies, /contact/ links to support
5. [ ] Run `python manage.py collectstatic` and test server

Current progress: Steps 1-3 complete
