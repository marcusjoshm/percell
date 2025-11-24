# Plugin Discovery - Simple Explanation

## The Simple Answer

**Yes, you need to put your plugin files in a specific folder: `percell/plugins/`**

That's it! Just drop your plugin file there and PerCell will find it automatically.

## How It Works (Simple Version)

Think of it like a library:

1. **The Library** = `percell/plugins/` folder
2. **Your Books** = Your plugin files (`.py` files)
3. **The Librarian** = PerCell's discovery system
4. **The Catalog** = The plugin registry

When you open the Plugins menu, PerCell acts like a librarian:
- Looks in the `percell/plugins/` folder
- Finds all your plugin files
- Adds them to the menu automatically
- No configuration needed!

## Where to Put Your Plugins

### ✅ Correct Location

```
percell/
└── plugins/
    ├── my_plugin.py          ← Put your plugin here!
    ├── another_plugin.py      ← Or here!
    └── yet_another.py         ← Or here!
```

### ❌ Wrong Locations

```
percell/
├── my_plugin.py              ← Won't be found here
├── scripts/
│   └── my_plugin.py          ← Won't be found here
└── plugins/
    └── subfolder/
        └── my_plugin.py       ← Won't be found here (unless you use plugin.json)
```

## Step-by-Step: Adding a Plugin

### Option 1: Create a New Plugin

1. **Generate a template:**
   ```bash
   python -m percell.plugins.template_generator MyPlugin
   ```
   This creates `percell/plugins/my_plugin.py` automatically.

2. **Edit the file** to add your logic.

3. **Done!** The plugin appears in the menu automatically.

### Option 2: Convert an Existing Script

1. **Convert your script:**
   ```bash
   python -m percell.plugins.converter my_script.py --name my_plugin
   ```
   This creates `percell/plugins/my_plugin.py`.

2. **Move the generated file** to `percell/plugins/` if it's not already there.

3. **Done!** The plugin appears in the menu automatically.

### Option 3: Manual Creation

1. **Create a file** in `percell/plugins/`:
   ```python
   # percell/plugins/my_plugin.py
   from percell.plugins.base import PerCellPlugin, PluginMetadata
   
   METADATA = PluginMetadata(
       name="my_plugin",
       version="1.0.0",
       description="My awesome plugin",
       author="Your Name"
   )
   
   class MyPlugin(PerCellPlugin):
       def execute(self, ui, args):
           ui.info("Hello from my plugin!")
           return args
   ```

2. **Save the file.**

3. **Done!** The plugin appears in the menu automatically.

## What Happens Behind the Scenes

When you open the Plugins menu, PerCell:

1. **Looks in the folder** `percell/plugins/`
2. **Finds all `.py` files** (except special ones like `__init__.py`)
3. **Reads each file** to find plugin classes or functions
4. **Adds them to the menu** automatically

It's like a smart assistant that:
- Knows where to look (`percell/plugins/`)
- Knows what to look for (plugin classes or functions)
- Knows how to add them (creates menu items)

## Common Questions

### Q: Do I need to register my plugin somewhere?

**A: No!** Just put the file in `percell/plugins/` and it's automatically discovered.

### Q: Do I need to restart PerCell?

**A: Yes, if you add a new plugin file.** The discovery happens when the Plugins menu is first opened, so you need to restart PerCell for new plugins to appear.

### Q: Can I put plugins in subfolders?

**A: Yes, but you need a `plugin.json` file.** See the advanced section below.

### Q: What if my plugin has errors?

**A: PerCell will skip it and show a warning.** Other plugins will still work.

### Q: Can I use the same plugin name twice?

**A: No, the second one will overwrite the first.** Use unique names.

## File Naming

### Good Names ✅
- `my_plugin.py`
- `image_processor.py`
- `data_analyzer.py`
- `batch_processor.py`

### Bad Names ❌
- `My Plugin.py` (spaces)
- `my-plugin.py` (hyphens - use underscores)
- `plugin.py` (too generic)
- `test.py` (might be ignored)

**Rule of thumb:** Use lowercase with underscores, like `my_plugin.py`

## Advanced: Subfolder Plugins

If you want to organize plugins in subfolders:

```
percell/plugins/
├── preprocessing/
│   ├── plugin.json          ← Required!
│   └── preprocessing.py
└── analysis/
    ├── plugin.json          ← Required!
    └── analysis.py
```

The `plugin.json` file tells PerCell:
- Plugin name
- Version
- Description
- Where to find the code

## Real-World Example

Let's say you have a script `analyze_cells.py` in your home directory:

```bash
# Step 1: Convert it to a plugin
python -m percell.plugins.converter ~/analyze_cells.py --name cell_analyzer

# Step 2: The converter creates percell/plugins/cell_analyzer.py
# (It might create it in the current directory, so check)

# Step 3: If it's not in percell/plugins/, move it:
mv cell_analyzer.py percell/plugins/

# Step 4: Restart PerCell

# Step 5: Open Plugins menu - your plugin is there!
```

## Summary

**The Simple Answer:**

1. **Put your plugin file in:** `percell/plugins/your_plugin.py`
2. **Restart PerCell**
3. **Open Plugins menu** - it's there automatically!

**That's it!** No configuration, no registration, no complicated setup. Just drop the file in the right folder and PerCell finds it.

## Quick Reference

| What | Where |
|------|-------|
| Plugin files | `percell/plugins/` |
| Template generator | `python -m percell.plugins.template_generator Name` |
| Script converter | `python -m percell.plugins.converter script.py` |
| Restart needed? | Yes, for new plugins |
| Configuration needed? | No! |

