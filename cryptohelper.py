
import tkinter as tk
from tkinter import font
import requests
import os
import json
import sys
from datetime import datetime
import threading


class RoundedButton(tk.Canvas):
    def __init__(self, parent, width, height, corner_radius, padding=0, color="#808080", fg="#000000", command=None, text="", font=None):
        tk.Canvas.__init__(self, parent, borderwidth=0, 
            relief="flat", highlightthickness=0, bg=parent.cget("bg"))
        self.command = command
        self.config(width=width + 2*padding, height=height + 2*padding)
        self.color = color
        self.fg = fg
        self.font = font
        self.width = width
        self.height = height
        self.corner_radius = corner_radius
        self.padding = padding
        self.text = text
        
        self.id = None
        self.text_id = None
        
        self.bind("<Button-1>", self._on_press)
        self.bind("<ButtonRelease-1>", self._on_release)
        self.draw()

    def draw(self):
        self.delete("all")
        if self.corner_radius > 0.5*self.width:
            self.corner_radius = 0.5*self.width
        if self.corner_radius > 0.5*self.height:
            self.corner_radius = 0.5*self.height

        rad = 2*self.corner_radius
        
        # Create a rounded polygon
        def _create_rounded_rect(x1, y1, x2, y2, r, **kwargs):
            points = (x1+r, y1, x1+r, y1, x2-r, y1, x2-r, y1, x2, y1, x2, y1+r, x2, y1+r, x2, y2-r, x2, y2-r, x2, y2, x2-r, y2, x2-r, y2, x1+r, y2, x1+r, y2, x1, y2, x1, y2-r, x1, y2-r, x1, y1+r, x1, y1+r, x1, y1)
            return self.create_polygon(points, **kwargs, smooth=True)

        self.id = _create_rounded_rect(
            self.padding, self.padding, 
            self.width+self.padding, self.height+self.padding, 
            rad, fill=self.color, outline=self.color
        )
        
        if self.text:
            self.text_id = self.create_text(
                self.width/2 + self.padding, 
                self.height/2 + self.padding, 
                text=self.text, 
                fill=self.fg,
                font=self.font
            )

    def _on_press(self, event):
        self.move(self.id, 1, 1)
        if self.text_id:
            self.move(self.text_id, 1, 1)

    def _on_release(self, event):
        self.move(self.id, -1, -1)
        if self.text_id:
            self.move(self.text_id, -1, -1)
        if self.command:
            self.command()
            
    def config(self, **kwargs):
        if 'text' in kwargs:
            self.text = kwargs.pop('text')
            self.itemconfig(self.text_id, text=self.text)
        if 'bg' in kwargs: # Ignore bg config for canvas to keep transparency fake
            pass
        super().config(**kwargs)

class CryptoWidget:
    def __init__(self):
        self.window = tk.Tk()
        self.window.title("Crypto helper")
        self.window.overrideredirect(True)  # Sin bordes
        self.window.attributes('-topmost', False)  # Siempre visible
        self.window.configure(bg='#520D30')
        
        # Configurar transparencia (opcional)
        self.window.attributes('-alpha', 0.9)
        
        # Fuentes
        self.title_font = font.Font(family="Comic Sans MS", size=10, weight="bold")
        self.price_font = font.Font(family="Comic Sans MS", size=12)
        self.change_font = font.Font(family="Comic Sans MS", size=9)
        self.btn_font = font.Font(family="Comic Sans MS", size=8)
        
        # Variables
        # All available cryptocurrencies
        self.available_cryptos = [
            {"id": "bitcoin", "symbol": "BTC", "name": "Bitcoin"},
            {"id": "chainlink", "symbol": "LINK", "name": "Chainlink"},
            {"id": "ethereum", "symbol": "ETH", "name": "Ethereum"},
            {"id": "uniswap", "symbol": "UNI", "name": "Uniswap"},
            {"id": "binancecoin", "symbol": "BNB", "name": "BNB"},
            {"id": "tether", "symbol": "USDT", "name": "Tether"}
        ]
        self.available_currencies = [
            {"id": "dollar", "symbol": "USD", "name": "Dollar"},
            {"id": "euro", "symbol": "EUR", "name": "Euro"},
            {"id": "pound", "symbol": "GBP", "name": "Pound"},
            {"id": "yen", "symbol": "JPY", "name": "Yen"},
            {"id": "won", "symbol": "KRW", "name": "Won"},
            {"id": "ruble", "symbol": "RUB", "name": "Ruble"},
            {"id": "peso chileno", "symbol": "CLP", "name": "Peso chileno"},
            {"id": "peso mexicano", "symbol": "MXN", "name": "Peso mexicano"},
            {"id": "peso colombiano", "symbol": "COP", "name": "Peso colombiano"},
            {"id": "peso argentino", "symbol": "ARS", "name": "Peso argentino"},
            {"id": "sol peruano", "symbol": "PEN", "name": "Sol peruano"}
        ]
        
        # Load memory
        # Load memory
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(__file__)
            
        self.memory_path = os.path.join(application_path, "memory.txt")
        self.cryptos = []
        # Set default currency
        self.selected_currency = self.available_currencies[0]

        if os.path.exists(self.memory_path):
            try:
                with open(self.memory_path, "r") as f:
                    data = json.load(f)
                    
                    # Handle cryptos (load IDs and find matching objects)
                    saved_cryptos = data.get("cryptos", [])
                    crypto_ids = []
                    for item in saved_cryptos:
                        if isinstance(item, dict):
                            crypto_ids.append(item.get('id'))
                        else:
                            crypto_ids.append(item)
                            
                    self.cryptos = [c for c in self.available_cryptos if c['id'] in crypto_ids]
                    
                    # Handle currency
                    saved_currency = data.get("currency")
                    currency_id = saved_currency
                    if isinstance(saved_currency, dict):
                        currency_id = saved_currency.get('id')
                        
                    found_currency = next((c for c in self.available_currencies if c['id'] == currency_id), None)
                    if found_currency:
                        self.selected_currency = found_currency

            except Exception as e:
                print(f"Error loading memory: {e}")
                
        # Fallback if no cryptos loaded
        if not self.cryptos:
            self.cryptos = self.available_cryptos[:3] 
        
        self.setup_ui()
        self.update_prices()
        
        # Actualizar cada 30 segundos
        self.auto_update()
        
        # Permitir mover el widget
        self.setup_dragging()

    def save_memory(self):
        data = {
            "cryptos": [c['id'] for c in self.cryptos],
            "currency": self.selected_currency['id']
        }
        try:
            with open(self.memory_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving memory: {e}")
        
    def setup_ui(self):
        # Marco principal
        self.main_frame = tk.Frame(self.window, bg='#1e1e1e', padx=10, pady=10)
        self.main_frame.pack()
        
        # Título
        self.title_label = tk.Label(
            self.main_frame,
            text="💰 Crypto helper",
            font=self.title_font,
            fg='#ffffff',
            bg='#520D30'
        )
        self.title_label.pack()
        
        # Separador
        tk.Frame(self.main_frame, height=1, bg='#333333').pack(fill='x', pady=5)
        
        # Contenedor para criptomonedas
        self.crypto_frame = tk.Frame(self.main_frame, bg='#520D30')
        self.crypto_frame.pack()
        
        # Labels para cada cripto
        self.crypto_labels = {}
        
        for crypto in self.cryptos:
            frame = tk.Frame(self.crypto_frame, bg='#520D30')
            frame.pack(anchor='w', pady=2)
            
            # Nombre
            name_label = tk.Label(
                frame,
                text=f"{crypto['symbol']}:",
                font=self.price_font,
                fg='#ffffff',
                bg='#520D30',
                width=8,
                anchor='w'
            )
            name_label.pack(side='left')
            
            # Precio
            price_label = tk.Label(
                frame,
                text="Cargando...",
                font=self.price_font,
                fg='#00ff00',
                bg='#520D30',
                width=12,
                anchor='w'
            )
            price_label.pack(side='left')
            
            # Cambio porcentual
            change_label = tk.Label(
                frame,
                text="",
                font=self.change_font,
                bg='#520D30'
            )
            change_label.pack(side='left', padx=(5,0))
            
            self.crypto_labels[crypto['id']] = {
                'price': price_label,
                'change': change_label
            }
        
        # Contenedor inferior (Hora + Botones + Versión)
        bottom_frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        bottom_frame.pack(fill='x', pady=(5,0))
        
        # Versión (Izquierda)
        version_label = tk.Label(
            bottom_frame,
            text="v0.5",
            font=("Comic Sans MS", 6),
            fg='#666666',
            bg='#1e1e1e'
        )
        version_label.pack(side='left', anchor='sw', padx=(0,5))
        
        # Hora de última actualización (Centro-ish)
        self.update_label = tk.Label(
            bottom_frame,
            text="",
            font=("Comic Sans MS", 7),
            fg='#888888',
            bg='#1e1e1e'
        )
        self.update_label.pack(side='left')
        
        # Frame para botones (Derecha)
        button_frame = tk.Frame(bottom_frame, bg='#1e1e1e')
        button_frame.pack(side='right')
        
        # Botón de moneda
        self.currency_btn = RoundedButton(
            button_frame,
            width=23,
            height=20,
            corner_radius=10,
            color='#146636',
            fg='#ffffff',
            command=self.open_currency,
            text=self.selected_currency['symbol'],
            font=self.btn_font
        )
        self.currency_btn.pack(side='left', padx=(0,3))

        # Botón de configuración
        settings_btn = RoundedButton(
            button_frame,
            width=23,
            height=20,
            corner_radius=10,
            color='#4444ff',
            fg='#ffffff',
            command=self.open_settings,
            text="⚙",
            font=self.btn_font
        )
        settings_btn.pack(side='left', padx=(0,3))
        
        # Botón para cerrar
        close_btn = RoundedButton(
            button_frame,
            width=23,
            height=20,
            corner_radius=10,
            color='#ff4444',
            fg='#ffffff',
            command=self.window.destroy,
            text="✕",
            font=self.btn_font
        )
        close_btn.pack(side='left')
        
    def fetch_prices(self):
        """Obtiene precios de CoinGecko API"""
        try:
            ids = ','.join([crypto['id'] for crypto in self.cryptos])
            currency_code = self.selected_currency['symbol'].lower()
            url = f"https://api.coingecko.com/api/v3/simple/price"
            params = {
                'ids': ids,
                'vs_currencies': currency_code,
                'include_24hr_change': 'true'
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            return data
            
        except Exception as e:
            print(f"Error: {e}")
            return None
    
    def update_prices(self):
        """Inicia la actualización de precios en segundo plano"""
        threading.Thread(target=self.fetch_prices_thread, daemon=True).start()

    def fetch_prices_thread(self):
        """Ejecuta la petición de red en un hilo separado"""
        data = self.fetch_prices()
        # Programar la actualización de la UI en el hilo principal
        self.window.after(0, lambda: self.update_ui(data))

    def update_ui(self, data):
        """Actualiza la interfaz gráfica (debe ejecutarse en el hilo principal)"""
        currency_code = self.selected_currency['symbol'].lower()
        
        # Mapeo simple de símbolos (se podría limpiar/mejorar)
        symbols = {
            'usd': '$', 'eur': '€', 'gbp': '£', 'jpy': '¥', 
            'krw': '₩', 'rub': '₽', 'clp': '$', 'mxn': '$', 
            'cop': '$', 'ars': '$', 'pen': 'S/'
        }
        currency_symbol = symbols.get(currency_code, '$')
        
        if data:
            for crypto in self.cryptos:
                crypto_id = crypto['id']
                if crypto_id in data:
                    price = data[crypto_id].get(currency_code, 0)
                    change = data[crypto_id].get(f'{currency_code}_24h_change', 0)
                    
                    # Formatear precio
                    if price > 1000:
                        price_text = f"{currency_symbol}{price:,.0f}"
                    elif price > 1:
                        price_text = f"{currency_symbol}{price:,.2f}"
                    else:
                        price_text = f"{currency_symbol}{price:.4f}"
                    
                    # Actualizar label de precio
                    self.crypto_labels[crypto_id]['price'].config(text=price_text)
                    
                    # Actualizar label de cambio
                    change_text = f"{change:+.2f}%"
                    change_color = '#00ff00' if change >= 0 else '#ff4444'
                    self.crypto_labels[crypto_id]['change'].config(
                        text=change_text,
                        fg=change_color
                    )
            
            # Actualizar hora
            current_time = datetime.now().strftime("%H:%M:%S")
            self.update_label.config(text=f"Actualizado: {current_time}")
    
    def rebuild_ui(self):
        """Reconstruye la interfaz con las criptomonedas seleccionadas"""
        # Destruir el frame de criptomonedas actual
        self.crypto_frame.destroy()
        
        # Recrear el frame
        self.crypto_frame = tk.Frame(self.main_frame, bg='#1e1e1e')
        self.crypto_frame.pack(after=self.title_label.master.children['!frame'], pady=(5,0))
        
        # Labels para cada cripto
        self.crypto_labels = {}
        
        for crypto in self.cryptos:
            frame = tk.Frame(self.crypto_frame, bg='#1e1e1e')
            frame.pack(anchor='w', pady=2)
            
            # Nombre
            name_label = tk.Label(
                frame,
                text=f"{crypto['symbol']}:",
                font=self.price_font,
                fg='#ffffff',
                bg='#1e1e1e',
                width=8,
                anchor='w'
            )
            name_label.pack(side='left')
            
            # Precio
            price_label = tk.Label(
                frame,
                text="Cargando...",
                font=self.price_font,
                fg='#00ff00',
                bg='#1e1e1e',
                width=12,
                anchor='w'
            )
            price_label.pack(side='left')
            
            # Cambio porcentual
            change_label = tk.Label(
                frame,
                text="",
                font=self.change_font,
                bg='#1e1e1e'
            )
            change_label.pack(side='left', padx=(5,0))
            
            self.crypto_labels[crypto['id']] = {
                'price': price_label,
                'change': change_label
            }
        
        # Actualizar precios inmediatamente
        self.update_prices()

    def set_currency(self, currency):
        self.selected_currency = currency
        # Actualizar texto del botón
        if hasattr(self, 'currency_btn'):
            self.currency_btn.config(text=currency['symbol'])
        self.update_prices()

    def open_currency(self):
        #Opción para cambiar la moneda :D
        currency_window = tk.Toplevel(self.window)
        currency_window.title("Moneda")
        currency_window.configure(bg='#520D30')
        
        # Posicionar la ventana de moneda relativa a la ventana principal
        main_x = self.window.winfo_x()
        main_y = self.window.winfo_y()
        
        # Calcular altura dinámica basada en items + padding
        window_height = len(self.available_currencies) * 35 + 50
        currency_window.geometry(f"350x{window_height}+{main_x}+{main_y}")
        currency_window.resizable(False, False)
        
        # Frame para botones
        button_frame = tk.Frame(currency_window, bg='#1e1e1e')
        button_frame.pack(anchor='e', pady=(5,0))
        
        # Monedas disponibles
        for currency in self.available_currencies:
            isSelected = False
            var = tk.BooleanVar()
            # Marcar si está actualmente seleccionada
            if currency['id'] == self.selected_currency['id']:
                var.set(True)
                isSelected = True

            def select_currency(curr=currency):
                self.set_currency(curr)
                self.save_memory()
                currency_window.destroy()

            cb = tk.Button(
                currency_window,
                text=currency['symbol'],
                command=select_currency,
                font=self.change_font,
                bg='#520D30',
                fg='#5C5C5C' if isSelected else '#ffffff',
                relief='flat',
                activebackground='#333333',
                activeforeground='#ffffff',
                width=20
            )
            cb.pack(anchor='w', pady=2, padx=10)

    def open_settings(self):
        #Opción para configurar las criptomonedas
        settings_window = tk.Toplevel(self.window)
        settings_window.title("Configuración de Criptomonedas")
        settings_window.configure(bg='#520D30')
        
        # Posicionar la ventana de configuración relativa a la ventana principal
        main_x = self.window.winfo_x()
        main_y = self.window.winfo_y()
        settings_window.geometry(f"350x350+{main_x}+{main_y}")
        settings_window.resizable(False, False)
        
        # Título
        title = tk.Label(
            settings_window,
            text="Selecciona hasta 3 criptomonedas",
            font=self.title_font,
            fg='#ffffff',
            bg='#520D30'
        )
        title.pack(pady=10)
        
        # Frame para checkboxes
        checkbox_frame = tk.Frame(settings_window, bg='#520D30')
        checkbox_frame.pack(pady=10)
        
        # Variables para checkboxes
        checkbox_vars = {}
        checkboxes = {}
        
        # Crear checkboxes para cada cripto disponible
        for crypto in self.available_cryptos:
            var = tk.BooleanVar()
            # Marcar si está actualmente seleccionada
            if any(c['id'] == crypto['id'] for c in self.cryptos):
                var.set(True)
            
            checkbox_vars[crypto['id']] = var
            
            cb = tk.Checkbutton(
                checkbox_frame,
                text=f"{crypto['name']} ({crypto['symbol']})",
                variable=var,
                font=("Comic Sans MS", 10),
                fg='#ffffff',
                bg='#520D30',
                selectcolor='#333333',
                activebackground='#520D30',
                activeforeground='#ffffff',
                command=lambda: self.validate_selection(checkbox_vars, checkboxes)
            )
            cb.pack(anchor='w', pady=2)
            checkboxes[crypto['id']] = cb
        
        # Label de advertencia
        warning_label = tk.Label(
            settings_window,
            text="",
            font=("Comic Sans MS", 8),
            fg='#ff4444',
            bg='#520D30'
        )
        warning_label.pack(pady=5)
        
        def validate_selection_wrapper():
            return self.validate_selection_static(checkbox_vars, checkboxes, warning_label)
        
        # Actualizar el comando de los checkboxes
        for crypto_id, cb in checkboxes.items():
            cb.config(command=validate_selection_wrapper)
        
        # Frame para botones
        button_frame = tk.Frame(settings_window, bg='#520D30')
        button_frame.pack(pady=20, padx=20)
        
        def save_settings():
            # Obtener criptos seleccionadas
            selected = [crypto for crypto in self.available_cryptos 
                       if checkbox_vars[crypto['id']].get()]
            
            if len(selected) == 0:
                warning_label.config(text="⚠ Debes seleccionar al menos 1 criptomoneda")
                return
            
            if len(selected) > 3:
                warning_label.config(text="⚠ Máximo 3 criptomonedas permitidas")
                return
            
            # Actualizar criptos seleccionadas
            self.cryptos = selected
            self.save_memory()
            
            # Reconstruir UI
            self.rebuild_ui()
            
            # Cerrar ventana
            settings_window.destroy()
        
        # Botón guardar
        save_btn = tk.Button(
            button_frame,
            text="Guardar",
            command=save_settings,
            font=("Comic Sans MS", 10),
            fg='#ffffff',
            bg='#00aa00',
            relief='flat',
            width=10
        )
        save_btn.pack(side='left', padx=5)
        
        # Botón cancelar
        cancel_btn = tk.Button(
            button_frame,
            text="Cancelar",
            command=settings_window.destroy,
            font=("Comic Sans MS", 10),
            fg='#ffffff',
            bg='#aa0000',
            relief='flat',
            width=10
        )
        cancel_btn.pack(side='left', padx=5)
    
    def validate_selection_static(self, checkbox_vars, checkboxes, warning_label):
        """Valida que no se seleccionen más de 3 criptomonedas"""
        selected_count = sum(1 for var in checkbox_vars.values() if var.get())
        
        if selected_count > 3:
            warning_label.config(text="⚠ Máximo 3 criptomonedas permitidas")
            # Deshabilitar checkboxes no seleccionados
            for crypto_id, cb in checkboxes.items():
                if not checkbox_vars[crypto_id].get():
                    cb.config(state='disabled')
        else:
            warning_label.config(text="")
            # Habilitar todos los checkboxes
            for cb in checkboxes.values():
                cb.config(state='normal')
    
    def validate_selection(self, checkbox_vars, checkboxes):
        """Método de compatibilidad para validación"""
        pass
    
    def auto_update(self):
        """Programa actualizaciones automáticas"""
        self.update_prices()
        # Programar próxima actualización en 30 segundos
        self.window.after(30000, self.auto_update)
    
    
    def setup_dragging(self):
        """Permite arrastrar el widget"""
        def start_drag(event):
            self.x = event.x
            self.y = event.y
        
        def drag(event):
            deltax = event.x - self.x
            deltay = event.y - self.y
            x = self.window.winfo_x() + deltax
            y = self.window.winfo_y() + deltay
            self.window.geometry(f"+{x}+{y}")
        
        # Vincular eventos a todo el widget
        self.window.bind('<Button-1>', start_drag)
        self.window.bind('<B1-Motion>', drag)
    
    def run(self):
        self.window.mainloop()

if __name__ == "__main__":
    widget = CryptoWidget()
    # Posicionar en la esquina superior izquierda
    widget.window.geometry("+50+50")
    widget.run()
    