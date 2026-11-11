from django import forms

from .models import Order

INPUT_CLASSES = "w-full border rounded-lg px-3 py-2 bg-white"


class CheckoutForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = [
            "full_name", "email", "phone",
            "address_line1", "address_line2",
            "city", "state", "pincode", "notes",
        ]
        widgets = {"notes": forms.Textarea(attrs={"rows": 2})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = INPUT_CLASSES
        self.fields["phone"].widget.attrs["placeholder"] = "10-digit mobile number"
        self.fields["pincode"].widget.attrs["placeholder"] = "6-digit PIN"
