
import evernote.edam.userstore.constants as UserStoreConstants
import evernote.edam.type.ttypes as Types
from evernote.edam.notestore import NoteStore

from evernote.api.client import EvernoteClient


def getUserShardId(authToken, userStore):
    """
    Get the User from userStore and return the user's shard ID
    """
    try:
        user = userStore.getUser(authToken)
    except (Errors.EDAMUserException, Errors.EDAMSystemException), e:
        print "Exception while getting user's shardID:"
        print type(e), e
        return None
    
    if hasattr(user, 'shardId'):
        return user.shardId
    return None

def shareSingleNote(authToken, noteStore, userStore, noteGuid, shardId=None):
    """
    Share a single note and return the public URL for the note
    """
    if not shardId:
        shardId = getUserShardId(authToken, userStore)
        if not shardId:
            raise SystemExit
 
    try:
        shareKey = noteStore.shareNote(authToken, noteGuid)
    except (EDAMNotFoundException, EDAMSystemException, EDAMUserException), e:
        print "Error sharing note:"
        print type(e), e
        return None
        
    EN_URL = 'https://sandbox.evernote.com'
    return "%s/shard/%s/sh/%s/%s" % \
        (EN_URL, shardId, noteGuid, shareKey)

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
    urls_and_contents = []
    for note in ourNoteList.notes:
        share_url = shareSingleNote(auth_token, note_store, user_store, note.guid)
        wholeNote = note_store.getNote(auth_token, note.guid, 
                        True, False, False, False)

        urls_and_contents.append((share_url, wholeNote))
    return (note_store, urls_and_contents)

