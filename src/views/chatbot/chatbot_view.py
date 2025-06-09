import flet as ft
from flet_core import colors
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

def get_chatbot_view(page: ft.Page) -> ft.Container:
    # Initialize chat history
    chat_history = ft.ListView(
        expand=True,
        spacing=10,
        padding=20,
        auto_scroll=True
    )

    # Initialize the model and tokenizer
    try:
        tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
        model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
        # Set pad token if not set
        if tokenizer.pad_token is None:
            tokenizer.pad_token = tokenizer.eos_token
            model.config.pad_token_id = model.config.eos_token_id
    except Exception as e:
        print(f"Error loading model: {e}")
        # Fallback to a simple response if model fails to load
        model = None
        tokenizer = None

    def get_bot_response(user_input):
        if model is None or tokenizer is None:
            return "I'm sorry, I'm having trouble connecting to my brain right now. Please try again later."

        try:
            # Encode the input with attention mask
            inputs = tokenizer(user_input + tokenizer.eos_token, return_tensors='pt', padding=True)
            input_ids = inputs['input_ids']
            attention_mask = inputs['attention_mask']
            
            # Generate response
            chat_response_ids = model.generate(
                input_ids,
                attention_mask=attention_mask,
                max_length=1000,
                pad_token_id=tokenizer.pad_token_id,
                no_repeat_ngram_size=3,
                do_sample=True,
                top_k=100,
                top_p=0.7,
                temperature=0.8
            )
            
            # Decode and return the response
            response = tokenizer.decode(chat_response_ids[:, input_ids.shape[-1]:][0], skip_special_tokens=True)
            return response if response else "I'm not sure how to respond to that."
        except Exception as e:
            print(f"Error generating response: {e}")
            return "I'm having trouble thinking right now. Please try again."

    def add_message(message, is_user=True):
        chat_history.controls.append(
            ft.Container(
                content=ft.Text(
                    message,
                    color="white" if is_user else colors.WHITE,
                    size=16
                ),
                bgcolor=colors.BLUE if is_user else colors.BLUE_GREY_900,
                padding=10,
                border_radius=10,
                alignment=ft.alignment.center_right if is_user else ft.alignment.center_left,
                margin=ft.margin.only(left=50 if is_user else 0, right=0 if is_user else 50)
            )
        )
        page.update()

    def on_send_click(e):
        if not message_input.value.strip():
            return

        # Add user message
        user_message = message_input.value.strip()
        add_message(user_message, True)
        message_input.value = ""

        # Get and add bot response
        bot_response = get_bot_response(user_message)
        add_message(bot_response, False)

        page.update()

    def on_keyboard_event(e: ft.KeyboardEvent):
        if e.key == "Enter" and not e.shift:
            on_send_click(e)

    # Message input field
    message_input = ft.TextField(
        hint_text="Type your message here...",
        expand=True,
        on_submit=on_send_click,
        multiline=False,
        color=colors.WHITE,
        bgcolor=colors.BLUE_GREY_900,
        border_color=colors.BLUE_GREY_700
    )

    # Send button
    send_button = ft.IconButton(
        icon=ft.Icons.SEND_ROUNDED,
        icon_color=colors.BLUE,
        on_click=on_send_click
    )

    # Input row
    input_row = ft.Row(
        controls=[
            message_input,
            send_button
        ],
        alignment=ft.MainAxisAlignment.SPACE_BETWEEN
    )

    # Welcome message
    add_message("Hello! I'm your Customer Service and Hospitality Assistant. How can I help you today?", False)

    # Main container
    chat_container = ft.Container(
        content=ft.Column(
            controls=[
                ft.Text("Customer Service & Hospitality Assistant", size=35, weight=ft.FontWeight.BOLD, color=colors.WHITE),
                ft.Container(
                    content=chat_history,
                    border=ft.border.all(1, colors.BLUE_GREY_700),
                    border_radius=10,
                    expand=True,
                    bgcolor=colors.BLUE_GREY_900
                ),
                input_row
            ],
            spacing=20,
            expand=True
        ),
        padding=20,
        bgcolor=colors.BLUE_GREY_900
    )

    # Add keyboard event handler
    page.on_keyboard_event = on_keyboard_event

    return chat_container 