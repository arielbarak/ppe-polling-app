import sys
import os
import json
import types

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from app.services.poll_service import PollService, poll_service, get_user_id
from app.models.poll import PollCreate, Vote


class FakeCrypto:
    @staticmethod
    def verify_signature(public_key, message, signature):
        # Accept any signature that equals 'validsig' for testing
        return signature == 'validsig'


def test_create_and_register_and_verify_user(monkeypatch):
    # Create a poll
    ps = PollService()
    poll = ps.create_poll(PollCreate(question='Q?', options=['A', 'B']))

    # Create two fake public keys
    pk1 = {'kty':'EC', 'x':'1', 'y':'1'}
    pk2 = {'kty':'EC', 'x':'2', 'y':'2'}

    # Register both
    import asyncio
    asyncio.get_event_loop().run_until_complete(ps.add_registrant(poll.id, pk1))
    asyncio.get_event_loop().run_until_complete(ps.add_registrant(poll.id, pk2))

    id1 = get_user_id(pk1)
    id2 = get_user_id(pk2)

    assert id1 in poll.registrants
    assert id2 in poll.registrants

    # Verify user: id1 verifies id2
    ps.verify_user(poll.id, id1, id2)
    assert id1 in poll.verifications
    assert id2 in poll.verifications
    assert id2 in poll.verifications[id1].has_verified


def test_record_vote_with_signature_check(monkeypatch):
    # Mock signature verification to be simple
    monkeypatch.setattr('app.services.poll_service.verify_signature', lambda pk, m, s: s == 'validsig')

    ps = PollService()
    poll = ps.create_poll(PollCreate(question='Q2?', options=['X', 'Y']))

    pk = {'kty':'EC', 'x':'abc', 'y':'def'}
    import asyncio
    asyncio.get_event_loop().run_until_complete(ps.add_registrant(poll.id, pk))
    user_id = get_user_id(pk)

    # Ensure verification requirement: add two verifiers for user
    poll.add_verification('verifier1', user_id)
    poll.add_verification('verifier2', user_id)

    # Submit valid vote
    vote = Vote(publicKey=pk, option='X', signature='validsig')
    updated = ps.record_vote(poll.id, vote)

    assert user_id in updated.votes
    assert updated.votes[user_id].option == 'X'

    # Submitting again should raise
    try:
        ps.record_vote(poll.id, vote)
        assert False, 'Expected ValueError for duplicate vote'
    except ValueError:
        pass
