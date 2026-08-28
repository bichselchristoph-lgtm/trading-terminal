---
id: c040
title: A sheet view of STORIES and BUGS, rebuilt by you from the folders
type: task
class: admin
unblocks: NOTHING
depends: none
---

# c040 — the tracker sheet

**Six steps, once. After that it is a menu item you click.**

The sheet is a **derived view**, exactly like `NOW.md`: rebuilt from the
folders, never written back. **Anything you type into it is lost on the next
rebuild, and that is correct rather than unfortunate** — two writable copies of
one tracker is how the duplicate-sheet failure happened before.

---

## Install

1. **New Google Sheet** in the Trading Terminal folder. Name it
   `TRACKERS derived view - LATEST`. The name matters: it should be impossible
   to mistake for a tracker.
2. **Extensions → Apps Script.**
3. **Select everything** in the `Code.gs` stub and **replace it** with the
   script below.
4. **Save** (the disk icon).
5. **Run** — pick `onOpen` in the function dropdown and press Run. It will ask
   for permission to read your Drive. **If it warns that Google has not
   verified the app, that is expected**: it is your own script in your own
   sheet, not a third party. Advanced → Go to the project → Allow.
6. **Reload the sheet.** A **Trackers** menu appears next to Help.

Then: **Trackers → Rebuild STORIES**, and **Rebuild BUGS**.

---

## What it does

Reads the folder, applies the supersede rule — **a row file outranks the base
file's line for the same id** — sorts by id, and writes the grid with a frozen
header row. Files ending `- OLD` are ignored. The `- LATEST.txt` readme is
ignored.

**It reports rather than repairs.** A row with the wrong number of fields, a
duplicate id, a file whose id does not match its name, a row file with more
than one line — each becomes a line on a `PROBLEMS` tab and a count in the
toast. **Nothing is silently padded or dropped.** A rebuild that finds nothing
wrong says `0 problems`, which is a different sentence from saying nothing.

Hover cell A1 after a rebuild for the counts.

---

## The script

```javascript
/**
 * Trading Terminal — derived tracker view.
 * Reads the STORIES and BUGS folders and writes them as grids.
 * This sheet is DERIVED. Edits here are lost on the next rebuild.
 */

var TRACKERS = {
  STORIES: {
    folderId: '1c8iFNrKyR4Mc6BHLNb3fmvI_PqwzXbMy',
    basePrefix: 'STORIES base',
    rowName: /^(S\d+) - LATEST\.txt$/
  },
  BUGS: {
    folderId: '1NhA7QT9CeJYHKzQlKWWpOjUYMZbBZE8W',
    basePrefix: 'BUGS base',
    rowName: /^(B-\d+) - LATEST\.txt$/
  }
};

function onOpen() {
  SpreadsheetApp.getUi()
    .createMenu('Trackers')
    .addItem('Rebuild STORIES', 'rebuildStories')
    .addItem('Rebuild BUGS', 'rebuildBugs')
    .addItem('Rebuild both', 'rebuildBoth')
    .addToUi();
}

function rebuildStories() { rebuild_('STORIES'); }
function rebuildBugs()    { rebuild_('BUGS'); }
function rebuildBoth()    { rebuild_('STORIES'); rebuild_('BUGS'); }

function rebuild_(name) {
  var cfg = TRACKERS[name];
  var problems = [];

  var baseText = null;
  var rowFiles = [];

  var files = DriveApp.getFolderById(cfg.folderId).getFiles();
  while (files.hasNext()) {
    var f = files.next();
    var title = f.getName();
    if (title.indexOf(' - OLD') !== -1) continue;
    if (title.indexOf(cfg.basePrefix) === 0) {
      if (baseText !== null) problems.push([title, 'second base file', '']);
      baseText = f.getBlob().getDataAsString('UTF-8');
      continue;
    }
    var m = cfg.rowName.exec(title);
    if (m) rowFiles.push({ file: f, idFromName: m[1] });
  }

  if (baseText === null) {
    SpreadsheetApp.getUi().alert('No base file found in the ' + name + ' folder. Nothing written.');
    return;
  }

  var lines = baseText.split(/\r?\n/).map(trim_).filter(nonEmpty_);
  var header = lines.shift().split('|').map(trim_);
  var width = header.length;

  var order = [];
  var byId = {};

  lines.forEach(function (line) {
    var fields = line.split('|');
    var id = trim_(fields[0]);
    if (byId[id]) problems.push([cfg.basePrefix, 'duplicate id in base', id]);
    byId[id] = fields;
    order.push(id);
    if (fields.length !== width) problems.push([id, 'field count ' + fields.length + ', header has ' + width, 'base file']);
  });

  var seenRowFile = {};
  rowFiles.forEach(function (rf) {
    var text = rf.file.getBlob().getDataAsString('UTF-8');
    var rows = text.split(/\r?\n/).map(trim_).filter(nonEmpty_);
    if (rows.length === 0) { problems.push([rf.file.getName(), 'empty file', '']); return; }
    if (rows.length > 1)  { problems.push([rf.file.getName(), 'more than one line, ' + rows.length, 'only the first was used']); }
    var fields = rows[0].split('|');
    var id = trim_(fields[0]);
    if (id !== rf.idFromName) problems.push([rf.file.getName(), 'id in file is ' + id, 'name says ' + rf.idFromName]);
    if (seenRowFile[id]) problems.push([rf.file.getName(), 'duplicate row file for id', id]);
    seenRowFile[id] = true;
    if (fields.length !== width) problems.push([id, 'field count ' + fields.length + ', header has ' + width, rf.file.getName()]);
    if (!byId[id]) order.push(id);
    byId[id] = fields;
  });

  order.sort(function (a, b) { return num_(a) - num_(b); });

  var grid = [header];
  order.forEach(function (id) {
    var fields = byId[id].slice(0, width);
    while (fields.length < width) fields.push('');
    grid.push(fields.map(trim_));
  });

  var ss = SpreadsheetApp.getActiveSpreadsheet();
  var sheet = ss.getSheetByName(name) || ss.insertSheet(name);
  sheet.clear();
  sheet.getRange(1, 1, grid.length, width).setValues(grid);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, width).setFontWeight('bold');
  sheet.getRange(1, 1, grid.length, width).setVerticalAlignment('top');

  var summary = order.length + ' rows · ' +
                Object.keys(seenRowFile).length + ' from row files · ' +
                problems.length + ' problems · rebuilt ' +
                Utilities.formatDate(new Date(), Session.getScriptTimeZone(), 'yyyy-MM-dd HH:mm');
  sheet.getRange(1, 1).setNote(summary + '\nDERIVED VIEW. Edits here are lost on the next rebuild.');

  writeProblems_(ss, name, problems);
  SpreadsheetApp.getActiveSpreadsheet().toast(summary, name, 8);
}

function writeProblems_(ss, name, problems) {
  var tab = name + ' PROBLEMS';
  var sheet = ss.getSheetByName(tab) || ss.insertSheet(tab);
  sheet.clear();
  if (problems.length === 0) {
    sheet.getRange(1, 1).setValue('0 problems');
    return;
  }
  var grid = [['what', 'found', 'detail']].concat(problems);
  sheet.getRange(1, 1, grid.length, 3).setValues(grid);
  sheet.setFrozenRows(1);
  sheet.getRange(1, 1, 1, 3).setFontWeight('bold');
}

function trim_(s)     { return String(s).replace(/^\s+|\s+$/g, ''); }
function nonEmpty_(s) { return s.length > 0; }
function num_(id)     { var m = /(\d+)/.exec(id); return m ? parseInt(m[1], 10) : 0; }
```

---

## What this does not do

**It does not write back.** There is no path from the sheet to the folders, and
there should not be — the design session is the tracker's only author, and a
second writer is a stop, not a merge.

**It does not run on a schedule.** You click it. A stale derived view that
refreshes itself is harder to notice than one you know you have not rebuilt.

**Nothing tests the script.** If Drive changes an API or a folder id moves, it
fails at the click rather than quietly producing a short grid — but no test
asserts that. Stated rather than assumed.

Signed-off by Christoph, Aug 24, 2026	