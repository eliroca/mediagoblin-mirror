/**
 * GNU MediaGoblin -- federated, autonomous media hosting
 * Copyright (C) 2011, 2012 MediaGoblin contributors.  See AUTHORS.
 *
 * This program is free software: you can redistribute it and/or modify
 * it under the terms of the GNU Affero General Public License as published by
 * the Free Software Foundation, either version 3 of the License, or
 * (at your option) any later version.
 *
 * This program is distributed in the hope that it will be useful,
 * but WITHOUT ANY WARRANTY; without even the implied warranty of
 * MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 * GNU Affero General Public License for more details.
 *
 * You should have received a copy of the GNU Affero General Public License
 * along with this program.  If not, see <http://www.gnu.org/licenses/>.
 */

'use strict';

(function () {
  // Small pill/gem indicator showing number of unseen comments. Comments are
  // shown inside the header panel which may be hidden.
  var notificationGem = document.querySelector('.notification-gem');
  notificationGem.addEventListener('click', function() {
    panel.show()
  });

  // Mark all comments seen feature.
  //
  // TODO: Currently broken due to bug in mark_comment_notification_seen().
  var mark_all_comments_seen = document.getElementById('mark_all_comments_seen');
  if (mark_all_comments_seen) {
    mark_all_comments_seen.href = '#';
    mark_all_comments_seen.onclick = function() {
      fetch(mark_all_comments_seen_url).then(function(response) {
        window.location.reload();
      });
    };
  }
})();
