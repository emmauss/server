"""
Gallery
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

"""
import os

from happypanda.common import exceptions, utils, constants
from happypanda.core.commands import database_cmd, io_cmd
from happypanda.core import message, db
from happypanda.interface import enums


# def add_gallery(galleries: list=[], paths: list=[]):
#    """
#    Add galleries to the database.

#    Args:
#        galleries: list of gallery objects
#        paths: list of paths to the galleries

#    Returns:
#        Gallery objects
#    """
#    return message.Message("works")


# def scan_gallery(paths: list=[], add_after: bool=False,
#                 ignore_exist: bool=True):
#    """
#    Scan folders for galleries

#    Args:
#        paths: list of paths to folders to scan for galleries
#        add_after: add found galleries after scan
#        ignore_exist: ignore existing galleries

#    Returns:
#        list of paths to the galleries
#    """
#    return message.Message("works")

def source_exists(item_type: enums.ItemType=enums.ItemType.Gallery,
                  item_id: int = 0,
                  check_all: bool=False):
    """
    Check if gallery/page source exists on disk

    Args:
        item_type: possible items are :py:attr:`.ItemType.Gallery`, :py:attr:`.ItemType.Page`
        item_id: id of item
        check_all: goes through all pages and checks them, default behaviour is to only check parent files/folders. Only relevant for :py:attr:`.ItemType.Gallery`

    Returns:
        .. code-block:: guess

            {
                'exists' : bool
                'missing' : [
                    {'id': int, 'item_type': item_type},
                    ...
                    ]
            }

    """

    item_type = enums.ItemType.get(item_type)

    _, db_model = item_type._msg_and_model((enums.ItemType.Gallery, enums.ItemType.Page))

    if item_type == enums.ItemType.Page:
        item = database_cmd.GetModelItemByID().run(db_model, {item_id}, columns=(db.Page.path,))
    elif item_type == enums.ItemType.Gallery:
        item = database_cmd.GetModelItemByID().run(db_model, {item_id}, columns=(db.Gallery.single_source,))

    if not item:
        raise exceptions.DatabaseItemNotFoundError(utils.this_function(),
                                                   "'{}' with id '{}' was not found".format(item_type.name,
                                                                                            item_id))
    else:
        item = item[0]

    paths = {}
    not_empty = True
    if item_type == enums.ItemType.Page:
        paths[item_id] = (item[0], item_type.value)
    elif item_type == enums.ItemType.Gallery:
        s = constants.db_session()
        if item and not check_all:
            p = s.query(db.Page.path).filter(db.Gallery.id == item_id).first()
            if p:
                paths[item_id] = (os.path.split(p[0])[0], item_type.value)
            else:
                not_empty = True
        else:
            ps = s.query(db.Page.id, db.Page.path).filter(db.Page.gallery_id == item_id).all()
            for p in ps:
                paths[p[0]] = (p[1], enums.ItemType.Page.value)
            not_empty = bool(ps)

    missing = []
    for t_id in paths:
        src, t_type = paths[t_id]
        try:
            e = io_cmd.CoreFS(src).exists
        except exceptions.ArchiveExistError:
            e = False
        if not e:
            missing.append({'id': t_id, 'item_type': t_type})

    return message.Identity("exists", {'exists': not missing and not_empty, 'missing': missing})


def get_page(page_id: int=None, gallery_id: int=None, number: int=None, prev: bool=False):
    """
    Get next/prev page by either gallery or page id

    Args:
        page_id: id of page
        gallery_id: id of gallery
        number: retrieve specific page number
        prev: by default next page is retrieved, to retrieve prev page set this to true

    Returns:
        Page object
    """
    if not (gallery_id or page_id):
        raise exceptions.APIError(
            utils.this_function(),
            "Either a gallery id or page id is required")

    if number is None:
        number = 0

    item = None

    if page_id:
        p = database_cmd.GetModelItemByID().run(db.Page, {page_id})[0]
        if number and p and number == p.number:
            item = p
        elif p:
            number = number or p.number
            gallery_id = p.gallery_id

    if not item:
        f = db.Page.number < number if prev else db.Page.number > number
        f = db.and_op(f, db.Page.gallery_id == gallery_id)
        item = database_cmd.GetModelItemByID().run(db.Page,
                                                   order_by=db.Page.number.desc() if prev else db.Page.number,
                                                   filter=f,
                                                   limit=1)
        if item:
            item = item[0]

    return message.Page(item) if item else None
