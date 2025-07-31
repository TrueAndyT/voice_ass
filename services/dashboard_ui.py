import json
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

class DashboardUI:
    """Dashboard UI configuration and layout management"""
    
    def __init__(self):
        self.config = self.get_default_config()
    
    def get_default_config(self):
        """Get default dashboard configuration"""
        return {
            "layout": {
                "header_size": 12,
                "body_ratio": 1,
                "performance_size": 3
            },
            "colors": {
                "header_style": "bold blue",
                "service_name_style": "cyan",
                "status_key_style": "bold green",
                "status_value_style": "white",
                "dashboard_border": "blue",
                "status_border": "cyan"
            },
            "columns": {
                "service": {"justify": "left", "min_width": 12},
                "cpu": {"justify": "center", "min_width": 6},
                "ram": {"justify": "center", "min_width": 6},
                "gpu": {"justify": "center", "min_width": 6},
                "vram": {"justify": "center", "min_width": 6}
            },
            "services": {
                "display_map": {
                    "stt": "Whisper",
                    "tts": "Kokoro", 
                    "Ollama": "Ollama",
                    "App (Main)": "App (Main)"
                }
            }
        }
    
    def load_config(self, config_file="dashboard_ui.json"):
        """Load configuration from JSON file"""
        try:
            with open(config_file, 'r') as f:
                loaded_config = json.load(f)
                # Merge with default config
                self.config.update(loaded_config)
        except FileNotFoundError:
            # Use default config if file doesn't exist
            pass
    
    def save_config(self, config_file="dashboard_ui.json"):
        """Save current configuration to JSON file"""
        with open(config_file, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def create_layout(self):
        """Create the main dashboard layout"""
        layout = Layout(name="root")
        layout.split(
            Layout(name="header", size=self.config["layout"]["header_size"]),
            Layout(ratio=self.config["layout"]["body_ratio"], name="body"),
        )
        layout["body"].split_row(Layout(name="stt"), Layout(name="llm"))
        layout["header"].split(
            Layout(name="main_header"),
            Layout(name="performance", size=self.config["layout"]["performance_size"])
        )
        return layout
    
    def create_system_resources_table(self, system_resources):
        """Create system resources table"""
        resources_table = Table(
            expand=True, 
            show_header=True, 
            header_style=self.config["colors"]["header_style"]
        )
        
        # Add columns based on config
        resources_table.add_column(
            "Service", 
            justify=self.config["columns"]["service"]["justify"],
            style=self.config["colors"]["service_name_style"],
            min_width=self.config["columns"]["service"]["min_width"]
        )
        resources_table.add_column(
            "CPU, %",
            justify=self.config["columns"]["cpu"]["justify"],
            min_width=self.config["columns"]["cpu"]["min_width"]
        )
        resources_table.add_column(
            "RAM, MB",
            justify=self.config["columns"]["ram"]["justify"],
            min_width=self.config["columns"]["ram"]["min_width"]
        )
        resources_table.add_column(
            "VRAM, MB",
            justify=self.config["columns"]["vram"]["justify"],
            min_width=self.config["columns"]["vram"]["min_width"]
        )
        
        # Add rows based on system resources data
        display_map = self.config["services"]["display_map"]
        for key, display_name in display_map.items():
            data = system_resources.get(key)
            if data:
                cpu = f"{data.get('cpu', 0):.1f}"
                ram = f"{data.get('ram', 0):.0f}"
                vram = data.get('vram', '-')
                resources_table.add_row(display_name, cpu, ram, str(vram))
            else:
                resources_table.add_row(display_name, "offline", "offline", "-")
        
        return resources_table
    
    def create_status_table(self, audio_level, assistant_state, intent):
        """Create status table with audio, state, intent"""
        status_table = Table.grid(padding=(0, 1))
        status_table.add_column(
            justify="right", 
            style=self.config["colors"]["status_key_style"]
        )
        status_table.add_column(
            justify="left", 
            style=self.config["colors"]["status_value_style"]
        )
        
        status_table.add_row("RMS Levels", audio_level)
        status_table.add_row("State", assistant_state)
        status_table.add_row("Intent", intent)
        
        return status_table
    
    def create_main_header_panel(self, system_resources, audio_level, assistant_state, intent):
        """Create the main header panel combining resources and status"""
        resources_table = self.create_system_resources_table(system_resources)
        status_table = self.create_status_table(audio_level, assistant_state, intent)
        
        top_grid = Table.grid(expand=True)
        top_grid.add_column(ratio=1)
        top_grid.add_column(ratio=1)
        top_grid.add_row(
            resources_table, 
            Panel(
                status_table, 
                title="Status", 
                border_style=self.config["colors"]["status_border"]
            )
        )
        
        return Panel(
            top_grid, 
            title="Voice Assistant Dashboard", 
            border_style=self.config["colors"]["dashboard_border"]
        )
    
    def create_performance_panel(self, perf_metrics):
        """Create performance metrics panel"""
        perf_text = " | ".join([f"{k}: {v}" for k, v in perf_metrics.items()])
        return Panel(Text(perf_text, justify="center"), title="Performance Metrics")
    
    def create_stt_panel(self, stt_output):
        """Create STT output panel"""
        return Panel(Text(stt_output), title="STT Output")
    
    def create_llm_panel(self, llm_output):
        """Create LLM output panel"""
        return Panel(Text(llm_output), title="LLM Output")

# Create default UI configuration file if it doesn't exist
if __name__ == "__main__":
    ui = DashboardUI()
    ui.save_config()
    print("Default dashboard UI configuration saved to dashboard_ui.json")
