import json
import logging
from typing import TYPE_CHECKING, Any, List, Optional

from ...app.models import App
from ...core.models import EventPayload
from ...payment import PaymentError, TransactionKind
from ...webhook.event_types import WebhookEventType
from ...webhook.payloads import (
    generate_checkout_payload,
    generate_customer_payload,
    generate_fulfillment_payload,
    generate_invoice_payload,
    generate_list_gateways_payload,
    generate_order_payload,
    generate_page_payload,
    generate_payment_payload,
    generate_product_deleted_payload,
    generate_product_payload,
    generate_product_variant_payload,
    generate_translation_payload,
)
from ..base_plugin import BasePlugin
from .tasks import trigger_webhook_sync, trigger_webhooks_async
from .utils import (
    from_payment_app_id,
    parse_list_payment_gateways_response,
    parse_payment_action_response,
)

if TYPE_CHECKING:
    from ...account.models import User
    from ...checkout.models import Checkout
    from ...core.notify_events import NotifyEventType
    from ...invoice.models import Invoice
    from ...order.models import Fulfillment, Order
    from ...page.models import Page
    from ...payment.interface import GatewayResponse, PaymentData, PaymentGateway
    from ...product.models import Product, ProductVariant
    from ...translation.models import Translation


logger = logging.getLogger(__name__)


class WebhookPlugin(BasePlugin):
    PLUGIN_ID = "mirumee.webhooks"
    PLUGIN_NAME = "Webhooks"
    DEFAULT_ACTIVE = True
    CONFIGURATION_PER_CHANNEL = False

    @classmethod
    def check_plugin_id(cls, plugin_id: str) -> bool:
        is_webhook_plugin = super().check_plugin_id(plugin_id)
        if not is_webhook_plugin:
            payment_app_data = from_payment_app_id(plugin_id)
            return payment_app_data is not None
        return is_webhook_plugin

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.active = True

    def order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.ORDER_CREATED)

    def order_confirmed(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.ORDER_CONFIRMED)

    def order_fully_paid(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.ORDER_FULLY_PAID)

    def order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.ORDER_UPDATED)

    def invoice_request(
        self,
        order: "Order",
        invoice: "Invoice",
        number: Optional[str],
        previous_value: Any,
    ) -> Any:
        if not self.active:
            return previous_value
        invoice_data = generate_invoice_payload(invoice)
        trigger_webhooks_async(invoice_data, WebhookEventType.INVOICE_REQUESTED)

    def invoice_delete(self, invoice: "Invoice", previous_value: Any):
        if not self.active:
            return previous_value
        invoice_data = generate_invoice_payload(invoice)
        trigger_webhooks_async(invoice_data, WebhookEventType.INVOICE_DELETED)

    def invoice_sent(self, invoice: "Invoice", email: str, previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        invoice_data = generate_invoice_payload(invoice)
        trigger_webhooks_async(invoice_data, WebhookEventType.INVOICE_SENT)

    def order_cancelled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.ORDER_CANCELLED)

    def order_fulfilled(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.ORDER_FULFILLED)

    def draft_order_created(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.DRAFT_ORDER_CREATED)

    def draft_order_updated(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.DRAFT_ORDER_UPDATED)

    def draft_order_deleted(self, order: "Order", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        order_data = generate_order_payload(order)
        trigger_webhooks_async(order_data, WebhookEventType.DRAFT_ORDER_DELETED)

    def fulfillment_created(self, fulfillment: "Fulfillment", previous_value):
        if not self.active:
            return previous_value
        fulfillment_data = generate_fulfillment_payload(fulfillment)
        trigger_webhooks_async(fulfillment_data, WebhookEventType.FULFILLMENT_CREATED)

    def customer_created(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        customer_data = generate_customer_payload(customer)
        trigger_webhooks_async(customer_data, WebhookEventType.CUSTOMER_CREATED)

    def customer_updated(self, customer: "User", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        customer_data = generate_customer_payload(customer)
        trigger_webhooks_async(customer_data, WebhookEventType.CUSTOMER_UPDATED)

    def product_created(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        product_data = generate_product_payload(product)
        trigger_webhooks_async(product_data, WebhookEventType.PRODUCT_CREATED)

    def product_updated(self, product: "Product", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        product_data = generate_product_payload(product)
        trigger_webhooks_async(product_data, WebhookEventType.PRODUCT_UPDATED)

    def product_deleted(
        self, product: "Product", variants: List[int], previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        product_data = generate_product_deleted_payload(product, variants)
        trigger_webhooks_async(product_data, WebhookEventType.PRODUCT_DELETED)

    def product_variant_created(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        product_variant_data = generate_product_variant_payload([product_variant])
        trigger_webhooks_async(
            product_variant_data, WebhookEventType.PRODUCT_VARIANT_CREATED
        )

    def product_variant_updated(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        product_variant_data = generate_product_variant_payload([product_variant])
        trigger_webhooks_async(
            product_variant_data, WebhookEventType.PRODUCT_VARIANT_UPDATED
        )

    def product_variant_deleted(
        self, product_variant: "ProductVariant", previous_value: Any
    ) -> Any:
        if not self.active:
            return previous_value
        product_variant_data = generate_product_variant_payload([product_variant])
        trigger_webhooks_async(
            product_variant_data, WebhookEventType.PRODUCT_VARIANT_DELETED
        )

    def checkout_created(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        checkout_data = generate_checkout_payload(checkout)
        event_payload = EventPayload.objects.create(payload=checkout_data)
        trigger_webhooks_async(event_payload, WebhookEventType.CHECKOUT_CREATED)

    def checkout_updated(self, checkout: "Checkout", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        checkout_data = generate_checkout_payload(checkout)
        trigger_webhooks_async(checkout_data, WebhookEventType.CHECKOUT_UPDATED)

    def notify(self, event: "NotifyEventType", payload: dict, previous_value) -> Any:
        if not self.active:
            return previous_value
        data = json.dumps({"notify_event": event, "payload": payload})
        trigger_webhooks_async(data, WebhookEventType.NOTIFY_USER)

    def page_created(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        page_data = generate_page_payload(page)
        trigger_webhooks_async(page_data, WebhookEventType.PAGE_CREATED)

    def page_updated(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        page_data = generate_page_payload(page)
        trigger_webhooks_async(page_data, WebhookEventType.PAGE_UPDATED)

    def page_deleted(self, page: "Page", previous_value: Any) -> Any:
        if not self.active:
            return previous_value
        page_data = generate_page_payload(page)
        trigger_webhooks_async(page_data, WebhookEventType.PAGE_DELETED)

    def translation_created(self, translation: "Translation", previous_value: Any):
        if not self.active:
            return previous_value
        translation_data = generate_translation_payload(translation)
        trigger_webhooks_async(translation_data, WebhookEventType.TRANSLATION_CREATED)

    def translation_updated(self, translation: "Translation", previous_value: Any):
        if not self.active:
            return previous_value
        translation_data = generate_translation_payload(translation)
        trigger_webhooks_async(translation_data, WebhookEventType.TRANSLATION_UPDATED)

    def __run_payment_webhook(
        self,
        event_type: str,
        transaction_kind: str,
        payment_information: "PaymentData",
        previous_value,
        **kwargs
    ) -> "GatewayResponse":
        if not self.active:
            return previous_value

        app = None
        payment_app_data = from_payment_app_id(payment_information.gateway)

        if payment_app_data is not None:
            app = (
                App.objects.for_event_type(event_type)
                .filter(pk=payment_app_data.app_pk)
                .first()
            )

        if not app:
            logger.warning(
                "Payment webhook for event %r failed - no active app found: %r",
                event_type,
                payment_information.gateway,
            )
            raise PaymentError(
                f"Payment method {payment_information.gateway} is not available: "
                "app not found."
            )

        webhook_payload = generate_payment_payload(payment_information)
        response_data = trigger_webhook_sync(event_type, webhook_payload, app)
        if response_data is None:
            raise PaymentError(
                f"Payment method {payment_information.gateway} is not available: "
                "no response from the app."
            )

        return parse_payment_action_response(
            payment_information, response_data, transaction_kind
        )

    def token_is_required_as_payment_input(self, previous_value):
        return False

    def get_payment_gateways(
        self,
        currency: Optional[str],
        checkout: Optional["Checkout"],
        previous_value,
        **kwargs
    ) -> List["PaymentGateway"]:
        gateways = []
        apps = App.objects.for_event_type(
            WebhookEventType.PAYMENT_LIST_GATEWAYS
        ).prefetch_related("webhooks")
        for app in apps:
            response_data = trigger_webhook_sync(
                event_type=WebhookEventType.PAYMENT_LIST_GATEWAYS,
                data=generate_list_gateways_payload(currency, checkout),
                app=app,
            )
            if response_data:
                app_gateways = parse_list_payment_gateways_response(response_data, app)
                if currency:
                    app_gateways = [
                        gtw for gtw in app_gateways if currency in gtw.currencies
                    ]
                gateways.extend(app_gateways)
        return gateways

    def authorize_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_AUTHORIZE,
            TransactionKind.AUTH,
            payment_information,
            previous_value,
            **kwargs,
        )

    def capture_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_CAPTURE,
            TransactionKind.CAPTURE,
            payment_information,
            previous_value,
            **kwargs,
        )

    def refund_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_REFUND,
            TransactionKind.REFUND,
            payment_information,
            previous_value,
            **kwargs,
        )

    def void_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_VOID,
            TransactionKind.VOID,
            payment_information,
            previous_value,
            **kwargs,
        )

    def confirm_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_CONFIRM,
            TransactionKind.CONFIRM,
            payment_information,
            previous_value,
            **kwargs,
        )

    def process_payment(
        self, payment_information: "PaymentData", previous_value, **kwargs
    ) -> "GatewayResponse":
        return self.__run_payment_webhook(
            WebhookEventType.PAYMENT_PROCESS,
            TransactionKind.CAPTURE,
            payment_information,
            previous_value,
            **kwargs,
        )

    # @staticmethod
    # def trigger_webhooks_async(payload, event_type):
    #     webhooks = _get_webhooks_for_event(event_type)
    #     deliveries = create_event_delivery_list_for_webhooks(
    #         webhooks=webhooks,
    #         event_payload=payload,
    #         event_type=event_type,
    #     )
    #     for delivery in deliveries:
    #         send_webhook_request.delay(delivery.id)
