from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button, Digits, DataTable, TabPane, TabbedContent, Static, Switch
from textual.widget import Widget
from textual.containers import Grid
from textual.reactive import reactive
from web_request import fetch, fetch_sync

BASE_URL = "http://fuso-ctl.local:8000"

class IvtTable(DataTable):
    table = reactive([])
    keys = ('index', 'label', 'voltage', 'current')

    def on_mount(self) -> None:
        self.set_interval(1, self.update_table)
        self.add_columns(*self.keys)
        self.cursor_type = "row"

    async def update_table(self):
        response = await fetch(f'{BASE_URL}/isa')
        if response and response['status'] == 'OK':
            self.table = response['result']
        else:
            self.table = [{}]

    def watch_table(self, table):
        self.clear()
        if len(table) > 0:
            self.add_rows([tuple(d[k] for k in self.keys) for d in table])

class BatteryTable(DataTable):
    table = reactive([])
    keys = ('index', 'id', 'switch', 'interlock', 'current', 'voltage', 'temp', 'ocv', 'soc')

    def on_mount(self) -> None:
        self.set_interval(1, self.update_table)
        self.add_columns(*self.keys)
        self.cursor_type = "row"

    async def update_table(self):
        response = await fetch(f'{BASE_URL}/bms')
        if response and response['status'] == 'OK':
            self.table = response['batteries']
        else:
            self.table = [{}]

    def watch_table(self, table):
        self.clear()
        if len(table) > 0:
            self.add_rows([tuple(d[k] for k in self.keys) for d in table])

class RelaySwitch(Switch):
    async def on_click(self) -> None:
        res = await fetch(f'{BASE_URL}/main/sw/{self.id}/{int(not self.value)}')
        print(res)

class RelayView(Widget):
    relays = reactive([])
    acdc = reactive([])

    def on_mount(self) -> None:
        self.set_interval(1, self.update_data)

    async def update_data(self):
        response = await fetch(f'{BASE_URL}/main/status')
        if response and response['status'] == 'OK':
            self.relays = response['value']['switches']
            self.acdc = response['value']['ACDC']
        else:
            self.relays = [{}]
            self.acdc = [{}]
        await self.recompose()

    def compose(self) -> ComposeResult:
        with Grid(id="relay_grid"):
            for relay in self.relays:
                yield Static(relay['name'], classes="switch_label")
                yield RelaySwitch(id=relay['name'], value=relay['status'])

    # async def watch_relays(self, relays):
    #     await self.recompose()

class EecTui(App):

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "eec_main.tcss"

    def compose(self) -> ComposeResult:
        yield Header()
        yield Footer()
        yield BatteryTable(id="battery_table")
        yield IvtTable(id="ivt_table")
        yield RelayView(id="relay_view")
        # with TabbedContent():
        #     with TabPane("Battery", id='battery_tab'):
        #         yield BatteryTable(id="battery_table")
        #         yield IvtTable(id="ivt_table")
        #     with TabPane("Relays", id='relay_tab'):
        #         yield RelayView(id="relay_view")

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )


if __name__ == "__main__":
    app = EecTui()
    app.run()