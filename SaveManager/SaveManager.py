import dearpygui.dearpygui as dpg
import shutil
import os
import json

dpg.create_context()

# Lists to store source, destination directories and names
sources = []
destinations = []
names = []

# File path for the JSON file
json_file_path = "save_folders.json"


def load_entries():
    global sources, destinations, names
    if os.path.exists(json_file_path):
        with open(json_file_path, "r") as f:
            entries = json.load(f)
            for entry in entries:
                names.append(entry["name"])
                sources.append(entry["source"])
                destinations.append(entry["destination"])
                dpg.add_text(
                    f"{entry['name']}: {entry['source']} -> {entry['destination']}",
                    parent="entry_list",
                )


def save_entries():
    entries = []
    for name, source, destination in zip(names, sources, destinations):
        entries.append({"name": name, "source": source, "destination": destination})
    with open(json_file_path, "w") as f:
        json.dump(entries, f, indent=4)
    dpg.set_value("status_text", "Entries saved successfully.")


def clear_entries_callback(sender, app_data):
    global sources, destinations, names
    sources.clear()
    destinations.clear()
    names.clear()

    # Clear the displayed entries
    dpg.delete_item("entry_list", children_only=True)
    dpg.set_value("status_text", "All entries cleared.")

    # Clear the JSON file
    if os.path.exists(json_file_path):
        os.remove(json_file_path)


def add_entry_callback(sender, app_data):
    name = dpg.get_value("name_input")

    if name and sources and destinations:
        current_source = sources[-1]  # Get the last added source
        current_destination = destinations[-1]  # Get the last added destination

        # Add the new entry
        names.append(name)
        dpg.add_text(
            f"{name}: {current_source} -> {current_destination}", parent="entry_list"
        )

        # Clear the displayed paths
        dpg.set_value("source_display", "")
        dpg.set_value("destination_display", "")
        dpg.set_value("name_input", "")  # Clear name input
        dpg.set_value("status_text", f"Added entry: {name}")
    else:
        dpg.set_value("status_text", "Please fill the name and select folders.")


def get_folder_size(folder):
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # Check if file exists to avoid errors
            if os.path.exists(fp):
                total_size += os.path.getsize(fp)
    return total_size


def copy_all_callback(sender, app_data):
    if not sources or not destinations or not names:
        dpg.set_value("status_text", "No entries to copy.")
        return

    # Reset progress bar
    total_pairs = len(sources)
    dpg.set_value("progress_bar", 0.0)
    dpg.set_value("status_text", "Copying directories...")
    dpg.show_item("progress_bar")

    for index in range(total_pairs):
        try:
            source_directory = sources[index]
            destination_directory = destinations[index]
            name = names[index]
            dest_path = os.path.join(
                destination_directory, os.path.basename(source_directory)
            )

            folder_size = get_folder_size(source_directory)

            # Skip copying if folder size exceeds 5 GB
            if folder_size > 5 * 1024 * 1024 * 1024:  # 5 GB in bytes
                dpg.set_value("error_text", f"Skipped '{name}' (size: {folder_size / (1024 * 1024 * 1024):.2f} GB) as it exceeds 5 GB.")
                continue  # Skip this folder and move to the next

            # Copy the directory
            shutil.copytree(source_directory, dest_path)
            dpg.set_value(
                "status_text",
                f"Copied '{name}' from '{source_directory}' to '{dest_path}' successfully.",
            )

            # Update progress bar
            progress = (index + 1) / total_pairs
            dpg.set_value("progress_bar", progress)

        except Exception as e:
            dpg.set_value("status_text", f"Error copying {name}: {str(e)}")

    dpg.set_value("status_text", "Copying completed.")
    dpg.hide_item("progress_bar")


def source_callback(sender, app_data):
    sources.append(app_data["file_path_name"])  # Store the selected source
    dpg.set_value(
        "source_display", app_data["file_path_name"]
    )  # Display the selected source path


def destination_callback(sender, app_data):
    destinations.append(app_data["file_path_name"])  # Store the selected destination
    dpg.set_value(
        "destination_display", app_data["file_path_name"]
    )  # Display the selected destination path


def cancel_callback(sender, app_data):
    dpg.set_value("status_text", "Operation was cancelled.")


# File Dialog for selecting source directory
dpg.add_file_dialog(
    directory_selector=True,
    show=False,
    callback=source_callback,
    tag="source_file_dialog",
    cancel_callback=cancel_callback,
    width=700,
    height=400,
)

# File Dialog for selecting destination directory
dpg.add_file_dialog(
    directory_selector=True,
    show=False,
    callback=destination_callback,
    tag="destination_file_dialog",
    cancel_callback=cancel_callback,
    width=700,
    height=400,
)

with dpg.font_registry():
    # Add font file and size
    custom_font = dpg.add_font("docs/font.otf", 20)

with dpg.window(tag="Primary Window"):
    dpg.add_text("Directory Copy Manager")
    dpg.add_separator()
    dpg.add_spacer(height=10)

    # Input for the name
    dpg.add_input_text(label="Name", tag="name_input")
    dpg.add_spacer(height=5)

    # Button to select source directory
    dpg.add_button(
        label="Select Source Directory",
        callback=lambda: dpg.show_item("source_file_dialog"),
    )
    dpg.add_text("", tag="source_display")  # Display for source path
    dpg.add_spacer(height=5)

    # Button to select destination directory
    dpg.add_button(
        label="Select Destination Directory",
        callback=lambda: dpg.show_item("destination_file_dialog"),
    )
    dpg.add_text("", tag="destination_display")  # Display for destination path
    dpg.add_spacer(height=5)

    # Button to add the entry
    dpg.add_button(label="Add Entry", callback=add_entry_callback)
    dpg.add_spacer(height=5)
    dpg.add_separator()

    # Container for displaying entries
    dpg.add_text("Entries will appear here:")
    with dpg.group(tag="entry_list"):
        # This will hold all entries
        pass

    # Button to copy all entries
    dpg.add_spacer(height=5)
    dpg.add_button(label="Copy All", callback=copy_all_callback)

    # Progress Bar
    dpg.add_spacer(height=10)
    dpg.add_progress_bar(
        tag="progress_bar", default_value=0.0, width=400, height=20, show=False
    )
    dpg.add_spacer(height=5)
    dpg.add_separator()

    # Horizontal group for Save and Clear All buttons
    dpg.add_spacer(height=5)
    with dpg.group(horizontal=True):
        dpg.add_button(label="Clear All Entries", callback=clear_entries_callback)
        dpg.add_button(label="Save Entries", callback=save_entries)

    dpg.add_spacer(height=5)
    dpg.add_text("", tag="status_text")
    dpg.add_text("", tag="error_text")

# Load entries on application start
load_entries()

# Necessary setup
dpg.bind_font(custom_font)
dpg.create_viewport(title="Save Manager", width=800, height=600)
dpg.setup_dearpygui()
dpg.show_viewport()
dpg.set_primary_window("Primary Window", True)
dpg.start_dearpygui()
dpg.destroy_context()