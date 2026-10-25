using Microsoft.Extensions.Primitives;

var builder = WebApplication.CreateBuilder(args);

// Registro de YARP vinculado a la seccion ReverseProxy del appsettings.json (hot-reload)
builder.Services.AddReverseProxy()
    .LoadFromConfig(builder.Configuration.GetSection("ReverseProxy"));

var app = builder.Build();

// Evidencia en consola: se imprime cada vez que appsettings.json cambia y se recarga
var seccion = app.Configuration.GetSection("ReverseProxy");
ChangeToken.OnChange(() => app.Configuration.GetReloadToken(), () =>
{
    var rutas = seccion.GetSection("Routes").GetChildren().Select(r => r.Key);
    var clusters = seccion.GetSection("Clusters").GetChildren()
        .Select(c => $"{c.Key}[{string.Join(", ", c.GetSection("Destinations").GetChildren().Select(d => d.Key))}]");
    Console.WriteLine($"[HOT-RELOAD] {DateTime.Now:HH:mm:ss} Configuracion recargada");
    Console.WriteLine($"             Rutas:    {string.Join(", ", rutas)}");
    Console.WriteLine($"             Clusters: {string.Join(" | ", clusters)}");
});

app.MapReverseProxy();

app.Run();
