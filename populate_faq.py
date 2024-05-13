from pymongo import MongoClient
from datetime import datetime

def get_mongo_connection():
    client = MongoClient("mongodb://offbeat_traveler:12345678@localhost:27017/travels")
    return client

def populate_faq():
    client = get_mongo_connection()
    db = client['travels']
    collection = db['faq']
    faqs = {
        "Flight": {
            "Book a flight using an airline credit": "To book a flight using your airline credit, please log in to your account, select your desired flight, and choose the 'Pay with Airline Credit' option at the payment stage.",
            "Airline-initiated schedule change": "If your flight schedule has been changed by the airline, you will receive an email with the new details. You can either accept the change or contact customer service for alternatives.",
            "Change your flight": "To change your flight, please visit the 'Manage Booking' section of our website, enter your booking details, and select the option to modify your flight times or dates."
        },
        "Refunds and Charges": {
            "Refund timelines, policies & processes": "Refunds typically take 7-10 business days to process. Our refund policy allows full refunds within 24 hours of booking, with some exceptions based on ticket type.",
            "Get a receipt for your booking": "You can obtain a receipt for your booking by logging into your account and visiting the 'Booking History' section, where you can download receipts directly.",
            "Payment security and options": "We ensure the security of your payments with industry-standard encryption. Available payment options include credit cards, PayPal, and direct bank transfers."
        },
        "Lodging": {
            "Change your hotel or vacation rental booking": "To change your booking, access your reservation details through your account and select 'Modify Booking'. Please note that changes may incur additional charges.",
            "Cancel your hotel or vacation rental booking": "Cancellations can be made online by going to your booking details and selecting 'Cancel Booking'. Please refer to the cancellation policy for potential fees.",
            "Check in and out of your hotel or vacation rental": "Check-in usually starts at 3 PM, and check-out must be done by 11 AM. Early check-in or late check-out can be requested by contacting the property directly."
        },
        "Packages": {
            "Change your vacation package": "Modifications to vacation packages can be made by contacting our support team, who can assist with changes in dates or destinations.",
            "Airline telephone numbers": "Airline contact numbers are available under the 'Airline Info' section of our website, where you can find detailed contact information for all our partner airlines.",
            "Cancel your vacation package": "To cancel a vacation package, please visit 'My Trips' and select the package you wish to cancel. Be aware that cancellation fees may apply."
        },
        "Cruise": {
            "Change or cancel your cruise booking": "You can change or cancel your cruise booking by logging into your account and managing your booking directly from there. Fees depend on the cancellation timeline.",
            "Booking mistakes and name changes": "For corrections to your booking or to change a name on the reservation, please contact our support center immediately.",
            "Book a cruise": "Browse our selection of cruises under the 'Cruise' section. Select your preferred cruise, cabin type, and travel dates to book your journey."
        },
        "Car": {
            "Change or cancel your car rental": "Changes to your car rental can be done online up to 48 hours before pickup. Cancellations can be made up to 24 hours in advance without fees.",
            "Booking mistakes and name changes": "If there is a mistake in your car rental booking or a name change is needed, please contact our customer service for prompt assistance.",
            "Car rental price quotes": "For price quotes on car rentals, please visit the 'Car Rental' section of our website and enter your travel dates and destination for instant quotes."
        },
        "Destination Services": {
            "Change or cancel your activity": "If you need to change or cancel a booked activity, please access your booking details from your profile and select the appropriate option.",
            "Booking mistakes and name changes": "For any errors in your bookings or to make a name change, please contact our customer service without delay.",
            "Add activities to your booking": "To add activities to your booking, go to 'Manage Booking', find your reservation, and select 'Add Activities'."
        },
        "Account": {
            "View your booking": "To view your current bookings, log in to your account and select 'My Bookings'. This section will show all your upcoming and past travel plans.",
            "Transportation Security Administration (TSA)": "For TSA guidelines and check-in procedures, please visit the TSA section on our website or contact TSA directly via their help line.",
            "Customs allowances for international travelers": "Customs allowances vary by destination. Check our 'Customs Information' page for details on what you can bring into and out of different countries."
        },
        "Privacy": {
            "Correct or update your account information": "To update your account details, log into your profile and select 'Account Settings', where you can edit your personal information securely.",
            "Information about your privacy": "We value your privacy. Please review our Privacy Policy for detailed information on how we collect, use, and protect your data.",
            "What privacy and data subject rights are available?": "You have rights under data protection laws, including the right to access, correct, delete, and restrict the processing of your data."
        },
        "Security": {
            "Payment security and options": "We use advanced security protocols to ensure that your payments are safe. Choose from several secure payment options when booking.",
            "Responsible disclosure of web vulnerabilities": "If you find a security vulnerability on our site, please contact us through the secure 'Web Vulnerability Disclosure' form.",
            "Beware of email scams (phishing)": "Be vigilant about email scams. Always verify the authenticity of requests for personal information by contacting us directly."
        },
        "Travel Alerts": {
            "Government travel alerts and warnings": "Stay updated with the latest government travel alerts and warnings by visiting our 'Travel Alerts' section regularly.",
            "Travel to, from or through Russia": "For current advice and restrictions on travel to, from, or through Russia, consult our dedicated travel advisory page.",
            "Bad weather and travel disruptions": "Check our 'Weather Alerts' section for updates on travel disruptions due to bad weather. Plan accordingly to minimize inconvenience."
        }
    }

    entries = []
    for category, qa_dict in faqs.items():
        for question, answer in qa_dict.items():
            faq_entry = {
                "category": category,
                "question": question,
                "answer": answer,
                "user_id": "admin",
                "timestamp": datetime.now()
            }
            entries.append(faq_entry)

    if entries:
        try:
            collection.insert_many(entries)
            print(f"Inserted {len(entries)} FAQs successfully.")
        except Exception as e:
            print(f"Failed to insert FAQs, error: {str(e)}")
    else:
        print("No FAQs to insert.")

    client.close()

if __name__ == "__main__":
    populate_faq()