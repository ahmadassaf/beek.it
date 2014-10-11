
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types
from evernote.edam.notestore import NoteStore

from evernote.api.client import EvernoteClient

def get_source_urls(auth_token):
    client = EvernoteClient(token=auth_token, sandbox=True)

    user_store = client.get_user_store()

    version_ok = user_store.checkVersion(
        "Evernote EDAMTest (Python)",
        UserStoreConstants.EDAM_VERSION_MAJOR,
        UserStoreConstants.EDAM_VERSION_MINOR
    )
    print "Is my Evernote API version up to date? ", str(version_ok)
    print ""
    if not version_ok:
        exit(1)

    note_store = client.get_note_store()

    # List all of the notebooks in the user's account
    notebooks = note_store.listNotebooks()

    # get all notes tagged 'beek'
    filter = NoteStore.NoteFilter()
    filter.words = "tag:beek"
    filter.ascending = False

    spec = NoteStore.NotesMetadataResultSpec()
    spec.includeTitle = True

    ourNoteList = note_store.findNotesMetadata(auth_token, filter, 0, 100, spec)
     
    wholeNotes = []

    for note in ourNoteList.notes:
        wholeNote = note_store.getNote(auth_token, note.guid, 
                        True, False, False, False) 
        print wholeNote.content
        wholeNotes.append(wholeNote)

    return [wholeNote['sourceURL'] for wholeNote in wholeNotes]

