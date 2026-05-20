import uuid
from typing import Callable, Dict, List
from dataclasses import dataclass, field


@dataclass
class Subscription:
    subscription_id: str
    event_type: str
    callback: Callable
    subscriber_name: str = ''

    @classmethod
    def create(cls, event_type: str, callback: Callable, subscriber_name: str = '') -> 'Subscription':
        return cls(
            subscription_id=f"sub-{uuid.uuid4().hex[:8]}",
            event_type=event_type,
            callback=callback,
            subscriber_name=subscriber_name
        )


class SubscriptionManager:
    def __init__(self):
        self._subscriptions: Dict[str, Subscription] = {}
        self._type_to_ids: Dict[str, List[str]] = {}

    def add(self, subscription: Subscription) -> str:
        self._subscriptions[subscription.subscription_id] = subscription
        if subscription.event_type not in self._type_to_ids:
            self._type_to_ids[subscription.event_type] = []
        self._type_to_ids[subscription.event_type].append(subscription.subscription_id)
        return subscription.subscription_id

    def remove(self, subscription_id: str) -> bool:
        if subscription_id in self._subscriptions:
            sub = self._subscriptions[subscription_id]
            if sub.event_type in self._type_to_ids:
                self._type_to_ids[sub.event_type] = [
                    sid for sid in self._type_to_ids[sub.event_type]
                    if sid != subscription_id
                ]
            del self._subscriptions[subscription_id]
            return True
        return False

    def get_by_type(self, event_type: str) -> List[Subscription]:
        subscription_ids = self._type_to_ids.get(event_type, [])
        subscriptions = []
        for sid in subscription_ids:
            if sid in self._subscriptions:
                subscriptions.append(self._subscriptions[sid])

        if '*' in self._type_to_ids:
            for sid in self._type_to_ids['*']:
                if sid in self._subscriptions and sid not in [s.subscription_id for s in subscriptions]:
                    subscriptions.append(self._subscriptions[sid])

        return subscriptions

    def get_all(self) -> List[Subscription]:
        return list(self._subscriptions.values())

    def clear(self):
        self._subscriptions.clear()
        self._type_to_ids.clear()
