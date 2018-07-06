'use strict';

// LOW LEVEL UTILS

const create_element = function(tag, options, ...children) {
  const el = document.createElement(tag);
  options = options || {};
  for (const k in options)
    if (k === 'events')
      for (name in options[k])
        el.addEventListener(name, options[k][name]);
    else if (k === 'dataset')
      for (name in options[k])
        el.dataset[name] = options[k][name];
    else if (k === 'innerHTML')
      el.innerHTML = options[k];
    else
      el.setAttribute(k, options[k]);
  for (const child of children)
    el.appendChild(typeof(child) === 'string' ? document.createTextNode(child) : child);
  return el;
};

const create_svg_element = function(tag, options, ...children) {
  const el = document.createElementNS('http://www.w3.org/2000/svg', tag);
  options = options || {};
  for (const k in options)
    if (k === 'events')
      for (name in options[k])
        el.addEventListener(name, options[k][name]);
    else
      el.setAttribute(k, options[k]);
  for (const child of children)
    el.appendChild(child);
  return el;
};

const union_dict = function(...elements) {
  if (elements.length == 1)
    return elements[0];
  const union = {};
  for (const elem of elements)
    Object.assign(union, elem);
  return union;
};

const async_sleep = ms => new Promise(resolve => setTimeout(resolve, ms));

// ART

const create_logo = function(options) {
  const h = 1.5;      // half line width
  const mh = 1.5;     // half margin
  const m = 2*mh;
  const i = m+h;      // horizontal distance from center to inner wall of stem
  const o = m+3*h;    // horizontal distance from center to outer wall of stem
  const c = 2*m+3*h;  // cut-off radius of w
  const l = m+2*h;    // stem length
  const s = 3*m+8*h;  // size of logo
  return (
    // NOTE: The .5 horizontal shift is to ensure crisp vertical lines on
    // non-retina screens.
    create_svg_element('svg', union_dict({viewBox: '-16.5 -16 32 32'}, options),
      create_svg_element('g', {transform: `translate(${-h-mh} ${-h-mh})`},
        create_svg_element('path', {stroke: 'none', d: `M -${o} 0 A ${o} ${o} 0 0 1 ${o} 0 L ${o} ${l} A ${h} ${h} 0 0 1 ${i} ${l} L ${i} 0 A ${i} ${i} 0 0 0 -${i} 0 L -${i} ${l} A ${h} ${h} 0 0 1 -${o} ${l} Z`})),
      create_svg_element('g', {transform: `translate(${h+mh} ${h+mh})`},
        create_svg_element('path', {stroke: 'none', d: `M -${o} -${l} A ${h} ${h} 0 0 1 -${i} -${l} L -${i} 0 A ${i} ${i} 0 0 0 ${i} 0 L ${i} -${l} A ${h} ${h} 0 0 1 ${o} -${l} L ${o} 0 A ${o} ${o} 0 0 1 -${o} 0 Z`}))));
};

const create_lock = function(options) {
  const hw = 6;  // half width
  const hh = 5;  // half height
  const so = 5;  // inner radius of the shackle
  const si = 4;  // outer radius of the shackle
  const sh = 2;  // length of the straight part of the shackle
  const su = 5;  // length of the straight part of the shackle unlocked
  return (
    create_svg_element('svg', union_dict({viewBox: '-16 -18 32 32'}, options),
      create_svg_element('path', {'class': 'show-if-theater-locked', stroke: 'none', d: `M ${-hw},${-hh} v ${2*hh} h ${2*hw} v ${-2*hh} h ${so-hw} v ${-sh} a ${so} ${so} 0 0 0 ${-2*so} 0 v ${sh} Z M ${-si} ${-hh} v ${-sh} a ${si} ${si} 0 0 1 ${2*si} 0 v ${sh} Z`}),
      create_svg_element('path', {'class': 'show-if-theater-unlocked', stroke: 'none', d: `M ${-hw},${-hh} v ${2*hh} h ${2*hw} v ${-2*hh} h ${so-hw} v ${-su} a ${si} ${si} 0 0 1 ${2*si} 0 v ${su} h ${so-si} v ${-su} a ${so} ${so} 0 0 0 ${-2*so} 0 v ${su} Z`})));
};

const log_level_paths = {
  0: 'M 4 -4 L -4 -4 L -4 4 L 4 4 M -4 0 L 1 0',
  1: 'M -4 -4 L -4 4 L 4 4 L 4 -4 M 0 4 L 0 -1',
  2: 'M -4 -4 L -4 4 L 4 4 L 4 -4',
  3: 'M -2 -4 L 2 -4 M 0 -4 L 0 4 M -2 4 L 2 4',
  4: 'M -4 -4 L 2 -4 L 4 -2 L 4 2 L 2 4 L -4 4 Z'
};

const create_boxed_icon = function(path, options) {
  if (window._n_boxed_icons == undefined)
    window._n_boxed_icons = 0;
  const path_id = `_boxed_icon_${window._n_boxed_icons}_m`;
  window._n_boxed_icons += 1;
  return (
    create_svg_element('svg', union_dict({viewBox: '-9 -9 18 18', style: 'width: 18px; height: 18px; border-radius: 1px;'}, options),
      create_svg_element('mask', {id: path_id},
        create_svg_element('path', {d: 'M -10 -10 L -10 10 L 10 10 L 10 -10 Z', fill: 'white', stroke: 'none'}),
        create_svg_element('path', {d: path, fill: 'none', 'stroke-width': '2', 'stroke-linecap': 'round', 'stroke-linejoin': 'round', stroke: 'black'})),
      create_svg_element('path', {mask: `url(#${path_id})`, d: 'M -9 -9 L -9 9 L 9 9 L 9 -9 Z', stroke: 'none'})));
};

const create_log_level_icon = function(level, options) {
  return create_boxed_icon(log_level_paths[level], options);
};

// LOG

// NOTE: This should match the log levels defined in `nutils/log.py`.
const LEVELS = ['error', 'warning', 'user', 'info', 'debug'];
const VIEWABLE = ['.jpg', '.jpeg', '.png', '.svg'];
// Make sure `VIEWABLE.filter(suffix => filename.endsWith(suffix))[0]` is always the longest match.
VIEWABLE.sort((a, b) => b.length - a.length);

const Log = class {
  constructor() {
    this.root = document.getElementById('log');
  }
  get state() {
    return {collapsed: this.collapsed, loglevel: this.loglevel};
  }
  set state(state) {
    // We deliberately ignore state changes, except during reloads (handled by
    // `init_elements` and `set loglevel` in the `window`s load event handler,
    // respectively).
  }
  get collapsed() {
    const collapsed = {};
    for (const context of document.querySelectorAll('#log .context.collapsed'))
      collapsed[context.dataset.id] = true;
    return collapsed;
  }
  get loglevel() {
    return parseInt(document.body.dataset.loglevel || 2);
  }
  set loglevel(level) {
    level = Math.max(0, Math.min(LEVELS.length-1, level));
    for (let i = 0; i < LEVELS.length; i++)
      document.body.classList.toggle('hide'+i, i > level);
    document.body.dataset.loglevel = level;
    const indicator = document.getElementById('log-level-indicator');
    if (indicator) {
      indicator.innerHTML = '';
      indicator.appendChild(create_log_level_icon(level));
    }
    if (this.state.loglevel !== level) {
      this.state.loglevel = level;
      update_state();
    }
  }
  keydown(ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey)
      return false;
    else if (ev.key.toLowerCase() == 'c') { // Collapse all.
      for (const context of document.querySelectorAll('#log .context'))
        if (context.lastElementChild && context.lastElementChild.classList.contains('end'))
          context.classList.add('collapsed');
      update_state();
    }
    else if (ev.key.toLowerCase() == 'e') { // Expand all.
      for (const context of document.querySelectorAll('#log .context'))
        context.classList.remove('collapsed');
      update_state();
    }
    else if (ev.key == '+' || ev.key == '=') { // Increase loglevel.
      this.loglevel = this.loglevel+1;
      update_state();
    }
    else if (ev.key == '-') { // Decrease loglevel.
      this.loglevel = this.loglevel-1;
      update_state();
    }
    else if (ev.key.toLowerCase() == 'f')
      this.toggle_follow();
    else
      return false;
    return true;
  }
  _cancel_follow_on_scroll_up(e) {

    if (window.log.root.scrollTop < window.log.root.scrollHeight - window.log.root.clientHeight) {
      document.body.classList.remove('follow');
      window.log.root.removeEventListener('scroll', window.log._cancel_follow_on_scroll_up);
    }
  }
  toggle_follow() {
    document.body.classList.toggle('follow');
    if (document.body.classList.contains('follow')) {
      this.root.scrollTop = this.root.scrollHeight - this.root.clientHeight;
      this.root.addEventListener('scroll', window.log._cancel_follow_on_scroll_up);
    }
  }
  *_reverse_contexts_iterator(context) {
    while (true) {
      if (!context || !context.classList.contains('context'))
        return;
      yield context;
      context = context.parentElement;
      if (!context)
        return;
      context = context.parentElement;
    }
  }
  init_elements(collapsed) {
    // Assign unique ids to context elements, collapse contexts according to
    // `state`.
    {
      let icontext = 0;
      for (const context of document.querySelectorAll('#log .context')) {
        context.dataset.id = icontext;
        context.classList.toggle('collapsed', collapsed[icontext] || false);
        icontext += 1;
        let label = [];
        for (let part of this._reverse_contexts_iterator(context))
          label.unshift((part.querySelector(':scope > .title') || {innerText: '?'}).innerText);
        context.dataset.label = label.join('/');
      }
    }

    // Assign (highest) log levels of children to context: loop over all items
    // and assign the item log level to parent context elements until the context
    // not has a higher level.
    for (const item of document.querySelectorAll('#log .item')) {
      const loglevel = parseInt(item.dataset.loglevel);
      let parent = item.parentElement;
      if (parent)
        parent = parent.parentElement;
      // NOTE: `parseInt` returns `NaN` if the `parent` loglevel is undefined and
      // `NaN < loglevel` is false.
      while (parent && parent.classList.contains('context') && !(parseInt(parent.dataset.loglevel) <= loglevel)) {
        parent.dataset.loglevel = loglevel;
        parent = parent.parentElement;
        if (parent)
          parent = parent.parentElement;
      }
    }

    // Link viewable anchors to theater.
    let ianchor = 0;
    for (const anchor of document.querySelectorAll('#log .item > a')) {
      const filename = anchor.innerText;
      const suffix = VIEWABLE.filter(suffix => filename.endsWith(suffix));
      if (!suffix.length)
        continue;
      const stem = filename.slice(0, filename.length - suffix[0].length);
      if (!stem)
        continue;
      const category = (stem.match(/^(.*?)[0-9]*$/) || [null, null])[1];
      anchor.dataset.href = anchor.href;
      anchor.addEventListener('click', this._plot_clicked);

      let context = null;
      let parent = anchor.parentElement;
      if (parent)
        parent = parent.parentElement;
      if (parent)
        parent = parent.parentElement;
      if (parent && parent.classList.contains('context'))
        context = parent;
      else
        context = {dataset: {}};

      anchor.id = `plot-${ianchor}`;
      ianchor += 1;
      theater.add_plot(anchor.href, anchor.id, category, context.dataset.id, (context.dataset.label ? context.dataset.label + '/' : '') + stem);
    }

    // Make contexts clickable.
    for (const title of document.querySelectorAll('#log .context > .title'))
      title.addEventListener('click', this._context_toggle_collapsed);
  }
  _plot_clicked(ev) {
    ev.stopPropagation();
    ev.preventDefault();
    window.history.pushState(window.history.state, 'log');
    theater.href = ev.currentTarget.dataset.href;
    document.body.dataset.show = 'theater';
    update_state();
  }
  _context_toggle_collapsed(ev) {
    // `ev.currentTarget` is the context title element (see https://developer.mozilla.org/en-US/docs/Web/API/Event/currentTarget)
    const context = ev.currentTarget.parentElement;
    context.classList.toggle('collapsed');
    update_state();
    ev.stopPropagation();
    ev.preventDefault();
  }
  scroll_into_view(anchor_id) {
    const anchor = document.getElementById(anchor_id);
    if (anchor) {
      let parent = anchor.parentElement;
      while (parent && parent.id != 'log') {
        if (parent.classList.contains('context'))
          parent.classList.remove('collapsed');
        parent = parent.parentElement;
      }
      anchor.scrollIntoView();
      update_state();
    }
  }
};

const IndentLog = class extends Log {
  constructor() {
    super();
    this.root = document.getElementById('log');
    this._fetched_bytes = 0;
    this._available_bytes = 0;
    this._pending_data = '';
    this._contexts = [];
    this._ncontexts = 0;
    this._nanchors = 0;
  }
  init_elements(collapsed) {
    // Make contexts clickable.
    for (const title of document.querySelectorAll('#log .context > .title'))
      title.addEventListener('click', this._context_toggle_collapsed);
  }
  _create_anchor(data, context_id, context_label) {
    const a = create_element('a', {href: data.href, dataset: {href: data.href}});
    if (data.thumb) {
      const im = create_element('img', {src: data.thumb});
      if (data.thumb_size) {
        im.width = data.thumb_size[0];
        im.height = data.thumb_size[1];
      }
      a.appendChild(im);
      a.appendChild(create_element('div', {'class': 'name'}, data.text));
      a.classList.add('thumb');
    }
    else
      a.appendChild(document.createTextNode(data.text));
    const suffix = VIEWABLE.filter(suffix => data.text.endsWith(suffix));
    if (!suffix.length)
      return a;
    const stem = data.text.slice(0, data.text.length - suffix[0].length);
    if (!stem)
      return a;
    const category = (stem.match(/^(.*?)[0-9]*$/) || [null, null])[1];
    a.addEventListener('click', this._plot_clicked);
    a.id = `plot-${this._nanchors}`;
    this._nanchors += 1;
    theater.add_plot(data.href, a.id, category, context_id, (context_label ? context_label + '/' : '') + stem);
    return a;
  }
  _parse_line(line) {
    const item = decodeURIComponent(line).match(/^([0-9]+)([a-z])(.*)$/);
    const ncontexts = parseInt(item[1]);
    const type = item[2];
    const value = item[3];
    // Close remaining contexts.
    if (ncontexts < this._contexts.length)
      this._contexts = this._contexts.slice(0, ncontexts);
    const context = this._contexts.length > 0 ? this._contexts[this._contexts.length-1] : {element: null, children: this.root};
    const loglevel = 'ewuid'.indexOf(type);
    if (type == 'c') {
      const children = create_element('div', {'class': 'children'});
      const title = create_element('div', {'class': 'title', events: {click: this._context_toggle_collapsed}}, value);
      const element = create_element('div', {'class': 'context', dataset: {id: this._ncontexts, label: (context.element && context.element.dataset.label ? context.element.label + '/' : '') + value}}, title, children);
      context.children.appendChild(element);
      this._contexts.push({element: element, children: children});
      this._ncontexts += 1;
    }
    else if (loglevel >= 0) {
      if (value[0] == 'a') {
        const context_id = context.element ? context.element.dataset.id : undefined;
        const context_label = context.element && context.element.dataset.label ? context.element.dataset.label : '';
        const a = this._create_anchor(JSON.parse(value.slice(1)), context_id, context_label);
        if (context.children.lastElementChild && context.children.lastElementChild.querySelector('a.thumb'))
          context.children.lastElementChild.appendChild(a);
        else
          context.children.appendChild(create_element('div', {'class': 'item', dataset: {loglevel: loglevel}}, a));
      }
      else if (value[0] == 't') {
        context.children.appendChild(create_element('div', {'class': 'item', dataset: {loglevel: loglevel}}, value.slice(1)));
      }
      else
        throw `Cannot parse log line: ${line}.`;
      // Apply log level to parent contexts.
      // NOTE: `parseInt` returns `NaN` if the `parent` loglevel is undefined
      // and `NaN < loglevel` is false.
      for (let i = this._contexts.length-1; i >= 0; i -= 1) {
        if (parseInt(this._contexts[i].element.dataset.loglevel) <= loglevel)
          break;
        this._contexts[i].element.dataset.loglevel = loglevel;
      }
    }
    else
      throw `Cannot parse log line: ${line}.`;
  }
  async check_progress() {
    const footer = document.getElementById('footer');
    const footer_status = document.getElementById('footer-status');
    while (true) {
      if (document.visibilityState == 'hidden') {
        // TODO: footer.classList.add('update-paused');
        await new Promise(resolve => {this._page_became_visible = resolve;});
        delete this._page_became_visible;
        // TODO: footer.classList.remove('update-paused');
      }
      try {
        const response = await fetch('progress.json', {cache: 'no-cache'});
        const data = await response.json();
        if (data.logpos !== undefined)
          this._available_bytes = data.logpos;
        if (this._fetched_bytes < this._available_bytes && this._data_arrived)
          this._data_arrived();
        footer_status.innerHTML = '';
        let first = true;
        for (const context of data.context) {
          if (!first)
            footer_status.appendChild(create_element('span', {'class': 'sep'}, ' • '));
          first = false;
          footer_status.appendChild(create_element('span', {'class': 'context', innerHTML: context}));
        }
        if (data.text) {
          if (!first)
            footer_status.appendChild(create_element('span', {'class': 'sep'}, ' • '));
          first = false;
          footer_status.appendChild(create_element('span', {'class': 'text', innerHTML: data.text}));
        }
        if (data.state == 'finished')
          break;
      }
      catch (e) {
        console.log(`failed to fetch/process progress file: ${e}`);
      }
      await async_sleep(1000);
    }
    this.finished = true;
  }
  init_log() {
    const logdata = document.getElementById('logdata');
    if (logdata == null)
      throw 'cannot find data section';
    this._pending_data = logdata.textContent;
    const i_newline = this._pending_data.indexOf('\n');
    if (i_newline < 0)
      throw 'cannot find data offset';
    this._fetched_bytes = parseInt(this._pending_data.slice(0, i_newline)) + this._pending_data.length;
    this._pending_data = this._pending_data.slice(i_newline+1);
    while (true) {
      const i_newline = this._pending_data.indexOf('\n');
      if (i_newline < 0)
        break;
      this._parse_line(this._pending_data.slice(0, i_newline));
      this._pending_data = this._pending_data.slice(i_newline+1);
    }
  }
  async update_log() {
    // TODO: Check support for range request first, see https://developer.mozilla.org/en-US/docs/Web/HTTP/Range_requests
    while (!this.finished || this._fetched_bytes < this._available_bytes) {
      if (this._fetched_bytes < this._available_bytes) {
        // The one byte overlap is added to ensure a 206 partial response even
        // if the server does not yet has the requested range (w/o overlap)
        // available.
        const response = await fetch('log.data', {cache: 'no-cache', headers: {'Range': `bytes=${this._fetched_bytes-1}-`}});
        if (response.status == 206 && response.headers.has('content-range') && response.headers.get('content-range').startsWith(`bytes ${this._fetched_bytes-1}-`)) {
          const new_fetched_bytes = parseInt(response.headers.get('content-range').split('-')[1])+1;
          if (new_fetched_bytes <= this._fetched_bytes-1)
            throw 'invalid partial response: content range end smaller than requested start';
          this._fetched_bytes = new_fetched_bytes;
          this._pending_data += (await response.text()).slice(1);
          while (true) {
            const i_newline = this._pending_data.indexOf('\n');
            if (i_newline < 0)
              break;
            this._parse_line(this._pending_data.slice(0, i_newline));
            this._pending_data = this._pending_data.slice(i_newline+1);
          }
          if (document.body.classList.contains('follow'))
            this.root.scrollTop = this.root.scrollHeight - this.root.clientHeight;
        }
        else if (response.status == 200) {
          if (this._fetched_bytes == 0) {
            let data = await response.text();
            const i_script = data.indexOf('<script id="logdata" type="application/octet-stream">');
            const i_start = data.indexOf('\n', i_script) + 1;
            data = data.slice(i_start);
            while (true) {
              const i_newline = data.indexOf('\n');
              if (i_newline < 0)
                break;
              this._parse_line(data.slice(0, i_newline));
              data = data.slice(i_newline+1);
            }
          }
          document.getElementById('log').appendChild(create_element('div', {}, 'Cannot fetch a partial log. Please reload manually.'));
          break;
        }
        else {
          document.getElementById('log').appendChild(create_element('div', {}, `Connection failed: ${response.status}.`));
          break;
        }
        await async_sleep(500); // Rate limit.
      }
      else {
        await new Promise(resolve => {this._data_arrived = resolve;});
        delete this._data_arrived;
      }
    }
  }
};

// THEATER

const Theater = class {
  constructor() {
    this.root = create_element('div', {id: 'theater', events: {'pointerdown': this.pointerdown.bind(this), 'pointerup': this.pointerup.bind(this)}});

    this.plots_per_category = {undefined: []};
    this.plots_per_context = {};
    this.info = {};
    this.touch_scroll_delta = 25;
  }
  add_plot(href, anchor_id, category, context, label, thumb) {
    const info = {href: href, anchor_id: anchor_id, category: category, index: this.plots_per_category[undefined].length, context: context, label: label, thumb: thumb};
    this.plots_per_category[undefined].push(href);
    if (category) {
      if (!this.plots_per_category[category])
        this.plots_per_category[category] = [];
      info.index_category = this.plots_per_category[category].length;
      this.plots_per_category[category].push(href);
    }
    if (!this.plots_per_context[context])
      this.plots_per_context[context] = [];
    this.plots_per_context[context].push(href);
    this.info[href] = info;
  }
  get locked() {
    return document.body.classList.contains('theater-locked');
  }
  set locked(locked) {
    if (locked === undefined)
      return;
    locked = Boolean(locked);
    if (this.locked == locked)
      return;
    document.body.classList.toggle('theater-locked', locked);
    update_state();
  }
  toggle_locked() {
    document.body.classList.toggle('theater-locked');
  }
  get overview() {
    return this.root.classList.contains('overview');
  }
  set overview(overview) {
    if (overview === undefined)
      return;
    overview = Boolean(overview);
    if (this.root.classList.contains('overview') == overview)
      return;
    if (overview)
      this._draw_overview();
    else
      this._draw_plot();
    this._update_selection();
    update_state();
  }
  toggle_overview() { this.overview = !this.overview; }
  get category() {
    return this.href ? this.info[this.href].category : undefined;
  }
  get index() {
    return this.href && (this.locked ? this.info[this.href].index_category : this.info[this.href].index);
  }
  get href() {
    return this._href;
  }
  set href(href) {
    if (href === undefined || this._href == href)
      return;
    const old_href = this._href;
    this._href = href;
    if (this.overview) {
      const old_context = old_href && this.info[old_href].context;
      const new_context = this.info[this._href].context;
      if (old_context != new_context)
        this._draw_overview();
    } else
      this._draw_plot();
    this._update_selection();
    document.getElementById('theater-label').innerText = this.info[this._href].label;
    update_state();
  }
  _draw_plot() {
    const plot = create_element('img', {src: this.href, 'class': 'plot', dataset: {category: this.info[this.href].category || ''}, events: {click: this._blur_plot.bind(this)}});
    this.root.innerHTML = '';
    this.root.classList.remove('overview');
    this.root.appendChild(plot);
  }
  _draw_overview() {
    this.root.innerHTML = '';
    this.root.classList.add('overview');
    this._update_overview_layout();
    for (const href of this.plots_per_context[this.info[this.href].context]) {
      const plot = create_element('img', {src: href, 'class': 'plot', dataset: {category: this.info[href].category || ''}, events: {click: this._focus_plot.bind(this)}});
      const plot_container3 = create_element('div', {'class': 'plot_container3'}, plot);
      const plot_container2 = create_element('div', {'class': 'plot_container2'}, plot_container3);
      if (this.info[href].category)
        plot_container2.appendChild(create_element('div', {'class': 'label'}, this.info[href].category));
      this.root.appendChild(create_element('div', {'class': 'plot_container1'}, plot_container2));
    }
  }
  _update_selection() {
    const category = this.category;
    for (const plot of this.root.querySelectorAll('img.plot')) {
      plot.classList.toggle('selected', plot.src == this.href);
      plot.classList.toggle('selected_category', plot.dataset.category == category);
    }
  }
  _update_overview_layout() {
    let nplots;
    try {
      nplots = this.plots_per_context[this.info[this.href].context].length;
    } catch (e) {
      return;
    }
    const plot_aspect = 640 / 480;
    const screen_width = window.innerWidth;
    const screen_height = window.innerHeight;
    let optimal_nrows = 1;
    let optimal_size = 0;
    for (let nrows = 1; nrows <= nplots; nrows += 1) {
      const ncols = Math.ceil(nplots / nrows);
      const size = Math.min(screen_width*screen_width/(ncols*ncols)/plot_aspect, screen_height*screen_height/(nrows*nrows)*plot_aspect);
      if (size > optimal_size) {
        optimal_nrows = nrows;
        optimal_size = size;
      }
    }
    let optimal_ncols = Math.ceil(nplots / optimal_nrows);
    this.root.style.gridTemplateColumns = Array(optimal_ncols).fill('1fr').join(' ');
    this.root.style.gridTemplateRows = Array(optimal_nrows).fill('1fr').join(' ');
  }
  _focus_plot(ev) {
    this.href = ev.currentTarget.src;
    this.overview = false;
    ev.preventDefault();
    ev.stopPropagation();
  }
  _blur_plot(ev) {
    this.overview = true;
    ev.preventDefault();
    ev.stopPropagation();
  }
  get current_plots() {
    return this.plots_per_category[this.locked && this.category || undefined];
  }
  next() {
    this.href = this.current_plots[this.index+1];
  }
  previous() {
    this.href = this.current_plots[this.index-1];
  }
  first() {
    this.href = this.current_plots[0];
  }
  last() {
    const plots = this.current_plots;
    this.href = plots[plots.length-1];
  }
  get state() {
    return {href: this.href, locked: this.locked, overview: this.overview};
  }
  set state(state) {
    if (state === undefined)
      return;
    this.href = state.href;
    if (state.locked !== undefined)
      this.locked = state.locked;
    if (state.overview !== undefined)
      this.overview = state.overview;
  }
  _open_log() {
    document.body.dataset.show = '';
    update_state(true);
    log.scroll_into_view(this.info[this.href].anchor_id);
  }
  keydown(ev) {
    if (ev.altKey || ev.ctrlKey || ev.metaKey)
      return false;
    else if (ev.key == ' ')
      this.locked = !this.locked;
    else if (ev.key == 'Tab')
      this.overview = !this.overview;
    else if (ev.key == 'ArrowLeft' || ev.key == 'PageUp' || ev.key.toLowerCase() == 'k')
      this.previous();
    else if (ev.key == 'ArrowRight' || ev.key == 'PageDown' || ev.key.toLowerCase() == 'j')
      this.next();
    else if (ev.key == 'Home' || ev.key == '^')
      this.first();
    else if (ev.key == 'End' || ev.key == '$')
      this.last();
    else if (ev.key == 'Escape')
      window.history.back();
    else if (ev.key.toLowerCase() == 'q')
      this._open_log();
    else
      return false;
    return true;
  }
  pointerdown(ev) {
    if (ev.pointerType != 'touch' || !ev.isPrimary)
      return;
    this._touch_scroll_pos = ev.screenY;
    // NOTE: This introduces a cyclic reference.
    this._pointer_move_handler = this.pointermove.bind(this);
    this.root.addEventListener('pointermove', this._pointer_move_handler);
  }
  pointermove(ev) {
    if (ev.pointerType != 'touch' || !ev.isPrimary)
      return;
    if (Math.abs(ev.screenY-this._touch_scroll_pos) > this.touch_scroll_delta) {
      if (ev.screenY < this._touch_scroll_pos - this.touch_scroll_delta) {
        const delta_index = Math.floor((this._touch_scroll_pos-ev.screenY) / this.touch_scroll_delta);
        const index = Math.max(0, this.index - delta_index);
        this._touch_scroll_pos = index == 0 ? ev.screenY : this._touch_scroll_pos - delta_index*this.touch_scroll_delta;
        this.href = this.current_plots[index];
      }
      else if (ev.screenY > this._touch_scroll_pos + this.touch_scroll_delta) {
        const delta_index = Math.floor((ev.screenY-this._touch_scroll_pos) / this.touch_scroll_delta);
        const max_index = this.current_plots.length - 1;
        const index = Math.min(max_index, this.index + delta_index);
        this._touch_scroll_pos = index == max_index ? ev.screenY : this._touch_scroll_pos + delta_index*this.touch_scroll_delta;
        this.href = this.current_plots[index];
      }
    }
  }
  pointerup(ev) {
    if (ev.pointerType != 'touch' || !ev.isPrimary)
      return;
    this._touch_scroll_pos = undefined;
    this.root.removeEventListener('pointermove', this._pointer_move_handler);
  }
};

// GLOBAL

// Disabled during initialization.  Will be enabled by the window load event
// handler.
let state_control = 'disabled';

const update_state = function(push) {
  if (state_control == 'disabled')
    return;
  let state;
  if (document.body.dataset.show == 'theater')
    state = {show: 'theater', theater: theater.state};
  else
    state = {show: '', log: log.state}
  if (push)
    window.history.pushState(state, 'log');
  else
    window.history.replaceState(state, 'log');
}

const apply_state = function(state) {
  const _state_control = state_control;
  state_control = 'disabled';
  if (state.show == 'theater')
    theater.state = state.theater;
  if (state.log)
    log.state = state.log;
  document.body.dataset.show = state.show || '';
  state_control = _state_control;
  // The collapsed state is not changed by going back or forward in the
  // history.  We do store the collapsed state in `window.history.state` to
  // preserve the collapsed state during a reload.  We call `update_state` here
  // because the restored state might have a different collapsed state.
  update_state();
}

const keydown_handler = function(ev) {
  if (ev.key == 'Escape' && document.body.classList.contains('droppeddown'))
    document.body.classList.remove('droppeddown');
  else if (document.body.dataset.show == 'theater' && theater.keydown(ev))
    ;
  else if (!document.body.dataset.show && log.keydown(ev))
    ;
  else if (ev.altKey || ev.ctrlKey || ev.metaKey)
    return;
  else if (ev.key == '?')
    document.body.classList.toggle('droppeddown');
  else if (ev.key.toLowerCase() == 'r') { // Reload.
    window.location.reload(true);
  }
  else if (ev.key.toLowerCase() == 'l') { // Load latest.
    if (document.body.dataset.latest)
      window.location.href = document.body.dataset.latest + '?' + Date.now();
  }
  else
    return;
  ev.stopPropagation();
  ev.preventDefault();
}

const visibilitychange_handler = function() {
  if (document.visibilityState == 'visible' && window.log._page_became_visible)
    window.log._page_became_visible();
};

const footer_clicked = function(e) {
  e.stopPropagation();
  e.preventDefault();
  window.log.toggle_follow();
};

window.addEventListener('load', function() {
  const grid = create_element('div', {'class': 'key_description'});
  const _add_key_description = function(cls, keys, description, _key) {
    grid.appendChild(create_element('div', {'class': cls+' keys', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); window.dispatchEvent(new KeyboardEvent('keydown', {key: _key})); }}}, keys.join('+')));
    grid.appendChild(create_element('div', {'class': cls}, description));
  }
  _add_key_description('', ['R'], 'Reload.', 'R');
  _add_key_description('', ['L'], 'Load latest.', 'L');
  _add_key_description('show-if-log', ['+'], 'Increase log verbosity.','+');
  _add_key_description('show-if-log', ['-'], 'Decrease log verbosity.','-');
  _add_key_description('show-if-log', ['C'], 'Collapse all contexts.','C');
  _add_key_description('show-if-log', ['E'], 'Expand all contexts.', 'E');
  _add_key_description('show-if-log', ['F'], 'Follow log.', 'F');
  _add_key_description('show-if-theater', ['TAB'], 'Toggle between overview and focus.', 'Tab');
  _add_key_description('show-if-theater', ['SPACE'], 'Lock to a plot category or unlock.', ' ');
  _add_key_description('show-if-theater', ['LEFT'], 'Show the next plot.', 'ArrowLeft');
  _add_key_description('show-if-theater', ['RIGHT'], 'Show the previous plot.', 'ArrowRight');
  _add_key_description('show-if-theater', ['Q'], 'Open the log at the current plot.', 'Q');
  _add_key_description('show-if-theater', ['ESC'], 'Go back.', 'Escape');

  if (document.body.classList.contains('indentlogger'))
    document.body.appendChild(create_element('div', {id: 'log'}));

  document.body.insertBefore(
    create_element('div', {id: 'header'},
      create_element('div', {'class': 'bar'},
        // logo
        create_element('a', {href: 'http://nutils.org/', title: 'nutils.org'}, create_logo({'class': 'button icon'})),
        // labels, only one is visible at a time
        create_element('div', {'class': 'show-if-log hide-if-droppeddown label'}, (document.body.dataset.scriptname || '') + ' ' + (document.body.dataset.funcname || '')),
        create_element('div', {id: 'theater-label', 'class': 'show-if-theater hide-if-droppeddown button label', title: 'exit theater and open log here', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); theater._open_log();}}}),
        create_element('div', {'class': 'show-if-droppeddown label'}, 'keyboard shortcuts'),
        // log level indicator, visible in log mode
        create_element('div', {'class': 'show-if-log icon small-icon-container', id: 'log-level-indicator'}),
        // category lock button, visible in theater mode
        create_lock({'class': 'show-if-theater button icon lock', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); theater.toggle_locked(); }}}),
        // hamburger
        create_element('div', {'class': 'hamburger icon button', events: {click: ev => { document.body.classList.toggle('droppeddown'); ev.stopPropagation(); ev.preventDefault(); }}},
          create_element('div'),
          create_element('div'),
          create_element('div'))),
      create_element('div', {'class': 'dropdown', events: {click: ev => { ev.stopPropagation(); ev.preventDefault(); }}},
        grid)),
    document.getElementById('log'));

  window.addEventListener('keydown', keydown_handler);
  window.addEventListener('popstate', ev => apply_state(ev.state || {}));
  window.addEventListener('resize', ev => window.requestAnimationFrame(theater._update_overview_layout.bind(theater)));

  window.theater = new Theater();
  window.log = document.body.classList.contains('indentlogger') ? new IndentLog() : new Log();
  document.body.appendChild(theater.root);
  document.body.appendChild(create_element('div', {'class': 'dropdown-catchall', events: {click: ev => { document.body.classList.remove('droppeddown'); ev.stopPropagation(); ev.preventDefault(); }}}));

  const state = window.history.state || {};
  window.log.init_elements((state.log || {}).collapsed || {});
  if (state.log && Number.isInteger(state.log.loglevel))
    log.loglevel = state.log.loglevel;
  else
    log.loglevel = LEVELS.indexOf('user');
  apply_state(state);
  state_control = 'enabled';

  window.log.init_log();
  if (document.body.classList.contains('indentlogger')) {
    document.body.appendChild(create_element('div', {id: 'footer', events: {click: footer_clicked}},
                                create_element('div', {id: 'footer-status'}),
                                create_element('div', {id: 'footer-follow', 'class': 'icon small-icon-container'},
                                  create_boxed_icon('M 4 -4 L -4 -4 L -4 4 M -4 0 L 1 0', {}))));
    window.log.check_progress();
    window.log.update_log();
    document.addEventListener('visibilitychange', visibilitychange_handler);
  }
});

// vim: sts=2:sw=2:et
