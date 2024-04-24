from motor import motor_asyncio
from os import getenv

# .env should be loaded by the bot. I totally expect this to break at some point
MONGO_URI = getenv("MONGO_URI")

_client = motor_asyncio.AsyncIOMotorClient(MONGO_URI)
db = _client.qcbot


async def get_doc(_id: str, collection: str, default=None):
    """Gets db.collection.doc[_id]"""
    collection = db[collection]

    doc = await collection.find_one({"_id": {"$eq": _id}}, {"_id": 0})
    return doc if doc else default


async def get_prop(_id: str, collection: str, prop, default=None):
    """db.collection.doc[_id].prop"""
    doc: dict = await get_doc(_id, collection, default={})
    return doc.get(str(prop), default)


async def del_prop(_id: str, collection: str, prop):
    collection = db[collection]
    await collection.update_one({"_id": {"$eq": _id}}, {"$unset": {str(prop): ""}})


async def set_prop(_id: str, collection: str, prop, value):
    collection = db[collection]
    await collection.update_one({"_id": {"$eq": _id}}, {"$set": {str(prop): value}}, upsert=True)


async def insert_doc(collection, document):
    collection = db[collection]
    await collection.insert_one(document)


async def find_docs(collection, query, limit=0):
    collection = db[collection]
    results = collection.find(query, limit=limit)
    return await flatten(results)


async def del_doc(_id: str, collection: str, key="_id"):
    """Completely removes a doc"""
    collection = db[collection]
    await collection.delete_one({key: {"$eq": _id}})


async def flatten(cursor):
    """Some operations such as aggregation return a fancy async cursor. Just make it into a list
    ONLY USE THIS IF THE RETURNED DATA ISN'T DUMMY THICC"""
    result = []
    async for i in cursor:
        result.append(i)
    return result
