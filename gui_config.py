import PySimpleGUI as sg
import os

def validate_time_format(timestr):
    """
    Expect MM:SS format. Return True if valid, False otherwise.
    """
    try:
        mm, ss = timestr.split(":")
        mm = int(mm)
        ss = int(ss)
        # We can allow any mm/ss range, but typically mm >= 0, ss between 0-59
        if mm < 0 or ss < 0 or ss > 59:
            return False
        return True
    except:
        return False

def format_segment(segment):
    """
    Return a string representation of the segment for display in the table.
    segment is a dict: {
        'start': 'MM:SS',
        'end': 'MM:SS',
        'bpm_or_transition': 'e.g. 120 or "transition"',
        'cover': 'path/to/image.png'
    }
    """
    return [
        segment['start'],
        segment['end'],
        segment['bpm_or_transition'],
        os.path.basename(segment['cover']) if segment['cover'] else ""
    ]

# Define the table headers
table_headings = ["Start", "End", "BPM/Transition", "Album Cover"]

def main():
    sg.theme("LightBlue2")

    # Data structure to hold all segments
    segments = []

    # Layout: top row for input fields, below that a table, then a row of buttons
    layout = [
        [sg.Text("Start (MM:SS)"), sg.Input(key="-START-", size=(8,1)),
         sg.Text("End (MM:SS)"), sg.Input(key="-END-", size=(8,1)),
         sg.Text("BPM or 'transition'"), sg.Input(key="-BPMTRANS-", size=(12,1)),
         sg.Text("Album Cover:"), 
         sg.Input(key="-COVER-", enable_events=True, visible=True, size=(20,1)), 
         sg.FileBrowse(file_types=(("Image Files", "*.png *.jpg *.jpeg *.bmp *.tiff"),), target="-COVER-")],
        
        [sg.Button("Add Segment", key="-ADD-"),
         sg.Button("Remove Selected", key="-REMOVE-"),
         sg.Button("Save to File", key="-SAVE-")],
        
        [sg.Table(
            values=[],
            headings=table_headings,
            key="-TABLE-",
            enable_events=True,
            auto_size_columns=True,
            display_row_numbers=False,
            justification="left",
            select_mode=sg.TABLE_SELECT_MODE_BROWSE,
            size=(60, 10)
        )]
    ]

    window = sg.Window("SDF Config GUI", layout, finalize=True)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break

        if event == "-ADD-":
            start_val = values["-START-"].strip()
            end_val = values["-END-"].strip()
            bpmtrans_val = values["-BPMTRANS-"].strip()
            cover_val = values["-COVER-"].strip()

            # Validation
            if not validate_time_format(start_val):
                sg.popup_error("Start time must be in MM:SS format!")
                continue
            if not validate_time_format(end_val):
                sg.popup_error("End time must be in MM:SS format!")
                continue
            if not bpmtrans_val:
                sg.popup_error("Please specify BPM or 'transition'.")
                continue

            # If user wants a BPM, ensure it's numeric (or user typed transition)
            # We'll just accept anything for now, but you can refine:
            # e.g. check if it's an integer or the word 'transition'.
            
            # Create a new segment dict
            seg = {
                "start": start_val,
                "end": end_val,
                "bpm_or_transition": bpmtrans_val,
                "cover": cover_val
            }
            segments.append(seg)

            # Update table
            table_data = [format_segment(s) for s in segments]
            window["-TABLE-"].update(values=table_data)

        elif event == "-REMOVE-":
            sel = window["-TABLE-"].get()
            if not sel:
                sg.popup_error("No segment selected!")
                continue
            # sel is a list of selected row indexes
            row_index = sel[0]
            if 0 <= row_index < len(segments):
                segments.pop(row_index)
                window["-TABLE-"].update(values=[format_segment(s) for s in segments])

        elif event == "-SAVE-":
            # Save to a durations-like file
            # We'll produce lines like "MM:SS-MM:SS 120" or "MM:SS-MM:SS transition"
            # Then we separately handle album covers if we want them in the same file or a second file
            save_path = sg.popup_get_file("Save durations.txt", save_as=True, default_extension=".txt", file_types=[("Text Files", "*.txt")])
            if not save_path:
                continue
            # Build lines
            lines = []
            for seg in segments:
                time_range = f"{seg['start']}-{seg['end']}"
                # If user typed a numeric BPM, store it as is, else "transition"
                # Or just store exactly what user typed (the code in main.py can interpret it)
                lines.append(f"{time_range} {seg['bpm_or_transition']}")
            
            # Write to file
            try:
                with open(save_path, "w") as f:
                    for line in lines:
                        f.write(line + "\n")
                sg.popup_ok(f"Saved to {save_path}!")
            except Exception as e:
                sg.popup_error(f"Could not save file:\n{str(e)}")

    window.close()

if __name__ == "__main__":
    main()