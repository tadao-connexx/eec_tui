from typing import Iterable
from textual import events, on
from textual.app import App, ComposeResult, SystemCommand
from textual.screen import Screen
from textual.widgets import Footer, Header, Button, DataTable, TabPane, TabbedContent, Input
from textual.reactive import reactive
from web_request import fetch, post

BASE_URL = "http://fuso-ctl.local:8000"

class IvtTable(DataTable):
    table = reactive([])
    keys = ('index', 'label', 'voltage', 'current')
    column_name = ('No.', 'Place', 'Voltage', 'Current')

    def on_mount(self) -> None:
        self.set_interval(1, self.update_table)
        self.add_columns(*self.column_name)
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
    keys = ('index', 'id', 'switch', 'interlock', 'voltage', 'current', 'ocv', 'temp', 'soc')
    column_name = ('No.', 'ID', 'Contactor', 'Interlock', 'Voltage', 'Current', 'OCV', 'Temp', 'SOC')

    def on_mount(self) -> None:
        self.set_interval(1, self.update_table)
        self.add_columns(*self.column_name)
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

    @on(DataTable.RowSelected)
    async def on_click_row(self, *args) -> None:
        res = await fetch(f'{BASE_URL}/bms/sw/{self.table[args[0].cursor_row]["index"]}/{self.table[args[0].cursor_row]["switch"] ^ 1}')
        print(res)

class RelayTable(DataTable):
    table = reactive([])
    keys = ('Name', 'Switch')

    def on_mount(self) -> None:
        self.set_interval(1, self.update_table)
        self.add_columns(*self.keys)
        self.cursor_type = "row"

    async def update_table(self):
        response = await fetch(f'{BASE_URL}/main/sw')
        if response and response['status'] == 'OK':
            self.table = response['value']
        else:
            self.table = [{}]

    def watch_table(self, table):
        self.clear()
        if len(table) > 0:
            names = tuple(d['name'] for d in table)
            sw = tuple('ON' if d['status'] else 'OFF' for d in table)
            self.add_rows(zip(names, sw))

    @on(DataTable.RowSelected)
    async def on_click_row(self, *args) -> None:
        res = await fetch(f'{BASE_URL}/main/sw/{self.table[args[0].cursor_row]["name"]}/{self.table[args[0].cursor_row]["status"] ^ 1}')
        print(res)


class PsuTable(DataTable):
    table = reactive({})
    keys = ('type', 'id', 'line_voltage', 'output_voltage', 'output_current', 'output_ref_volt', 'current_limit', 'temperature', 'status')
    column_name = ('Type', 'ID', 'In(V)', 'Out(V)', 'Out(A)', 'Target(V)', 'Limit(A)', 'Temp(C)', 'Status')

    def on_mount(self) -> None:
        self.set_interval(1, self.update_table)
        self.add_columns(*self.column_name)
        self.cursor_type = "row"

    async def update_table(self):
        response = await fetch(f'{BASE_URL}/main/psu')
        if response and response['status'] == 'OK':
            self.table = response['value']
        else:
            self.table = {}

    def get_flattened_table(self, table):
        for i in range(len(table)):
            table2 = [table[i][k] for k in self.keys[2:]]
            num = len(table[i][self.keys[2]])
            types = [table[i][self.keys[0]]] * num
            ids = [table[i][self.keys[1]]] * num
            return tuple(zip(types, ids, *table2))

    def watch_table(self, table):
        self.clear()
        if table and table.get('ACDC', None):
            self.add_rows(self.get_flattened_table(table['ACDC']))
        if table and table.get('DCDC', None):
            self.add_rows(self.get_flattened_table(table['DCDC']))

class PsuButton(Button):
    voltage: Input|None = None
    current: Input|None = None
    async def on_click(self) -> None:
        params = {
            'psu_type': 'AC',
            'unit': 0,
        }
        if self.label == 'OFF':
            params['run'] = 0
            res = await post(f'{BASE_URL}/main/psu', params)
            print(res)
        elif self.label == 'ON' and self.voltage and self.current:
            v = str(self.voltage.value)
            params['run'] = 1
            params['voltage'] = v
            params['current'] = str(self.current.value)
            params['hi_mode'] = int(float(v) > 500)
            res = await post(f'{BASE_URL}/main/psu', params)
            print(res)

class EecTui(App):

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode")]
    CSS_PATH = "eec_main.tcss"
    input_voltage = Input(placeholder="Voltage")
    input_current = Input(placeholder="Current")
    psu_off = PsuButton("OFF", id='psu_off', variant='error')
    psu_on = PsuButton("ON", id='psu_on', variant='success')

    def compose(self) -> ComposeResult:
        self.psu_on.voltage = self.input_voltage
        self.psu_on.current = self.input_current
        yield Header()
        yield Footer()
        with TabbedContent():
            with TabPane("Battery", id='battery_tab'):
                yield BatteryTable(id="battery_table")
                yield IvtTable(id="ivt_table")
            with TabPane("Relays", id='relay_tab'):
                yield RelayTable(id="relay_table")
            with TabPane("PSU", id='psu_tab'):
                yield PsuTable(id="psu_table")
                yield self.input_voltage
                yield self.input_current
                yield self.psu_on
                yield self.psu_off

    def action_toggle_dark(self) -> None:
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def get_system_commands(self, screen: Screen) -> Iterable[SystemCommand]:
        yield from super().get_system_commands(screen)
        yield SystemCommand("turn-on-system", "Turn on system", self.send_turn_on_system)
        yield SystemCommand("turn-off-system", "Turn off system", self.send_turn_off_system)

    async def send_turn_on_system(self):
        await fetch(f'{BASE_URL}/main/button/{7}')

    async def send_turn_off_system(self):
        await fetch(f'{BASE_URL}/main/button/{8}')


if __name__ == "__main__":
    app = EecTui()
    app.run()