from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Button, Digits, DataTable, TabPane, TabbedContent, Static, Switch, Checkbox
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

class PsuTable(DataTable):
    table = reactive([])
    keys = ('line_voltage', 'output_voltage', 'output_current', 'output_ref_volt', 'current_limit', 'temperature', 'status')

    def on_mount(self) -> None:
        self.add_columns(*self.keys)
        self.cursor_type = "row"

    def watch_table(self, table):
        self.clear()
        if len(table) > 0:
            flattened_table = []
            for i in range(len(table)):
                table2 = [table[i][k] for k in self.keys]
                # flattened_table.extend(zip(*table2))
                self.add_rows(tuple(zip(*table2)))
            # self.add_rows(flattened_table)


class RelaySwitch(Switch):
    async def on_click(self) -> None:
        res = await fetch(f'{BASE_URL}/main/sw/{self.id}/{int(not self.value)}')

class RelayView(Widget):
    relays = reactive([])
    acdc = PsuTable(id="acdc_table")

    def on_mount(self) -> None:
        self.set_interval(1, self.update_data)

    async def update_data(self):
        response = await fetch(f'{BASE_URL}/main/status')
        if response and response['status'] == 'OK':
            self.relays = response['value']['switches']
            self.acdc.table = response['value']['ACDC']
        else:
            self.relays = [{}]
            self.acdc.table = []
        await self.recompose()

    def compose(self) -> ComposeResult:
        with Grid(id="relay_grid"):
            for relay in self.relays:
                yield Static(relay['name'], classes="switch_label")
                yield RelaySwitch(id=relay['name'], value=relay['status'])
        yield self.acdc

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