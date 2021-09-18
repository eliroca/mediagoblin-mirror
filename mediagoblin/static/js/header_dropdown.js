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

var panel = {};

(function() {
  // The header drop-down header panel defaults to open until you explicitly
  // close it. After that, the panel open/closed setting will persist across
  // page loads.
  var panel_elem = document.getElementById('header_dropdown');
  var up_arrow_elem = document.querySelector('.header_dropdown_up');
  var down_arrow_elem = document.querySelector('.header_dropdown_down');

  function hide(elem) {
    elem.style.display = 'none';
  }

  function show(elem) {
    elem.style.display = '';
  }

  function isDisplayed(elem) {
    return elem.style.display === '';
  }

  function toggle(elem) {
    if (isDisplayed(elem)) {
      hide(elem);
    }
    else {
      show(elem);
    }
  }

  function showPanel() {
    localStorage.removeItem('panel_closed');
    show(panel_elem);
    show(up_arrow_elem);
    hide(down_arrow_elem);
  }

  function hidePanel() {
    localStorage.setItem('panel_closed', 'true');
    hide(panel_elem);
    hide(up_arrow_elem);
    show(down_arrow_elem);
  }

  function togglePanel() {
    // Toggle and persist the panel status.
    if (isDisplayed(panel_elem)) {
      hidePanel();
    }
    else {
      showPanel()
    }
  }

  // Initialise the panel status when page is loaded.
  up_arrow_elem.addEventListener('click', togglePanel);
  down_arrow_elem.addEventListener('click', togglePanel);
  if (localStorage.getItem('panel_closed')) {
    hidePanel();
  }
  else {
    showPanel();
  }

  // Export some functionality for use in other modules.
  panel.show = showPanel;
})();
