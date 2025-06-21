# import requests
#
# from odoo.exceptions import UserError
#
#
# class VendorNotificationService:
#     @staticmethod
#     def notify_new_rfq_created(vendor_id, rfq_id):
#         # url = f"{ExternalApiConfig.get_vendor_notification_webhook()}"
#         #
#         # target_data = {
#         #     "vendorId": vendor_id,
#         #     "title": "new rfq created",
#         #     "message": f"rfq_id : {rfq_id}"
#         # }
#         #
#         # response = requests.put(url, json=target_data, headers=ExternalAuthUtil.get_vdm_auth_headers(), verify=False)
#         #
#         # try:
#         #     response.raise_for_status()
#         #     return True
#         # except requests.exceptions.HTTPError as err:
#         #     # TODO : handle the error message
#         #     return False
#         pass
