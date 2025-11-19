using System;
using System.Net;
using System.Net.Sockets;
using System.Text;
using System.Threading;
using UnityEngine;

public class Receiver
{
    private readonly int port;
    private TcpListener listener;
    private Thread listenerThread;
    private bool running = false;

    public Action<string> OnMessageReceived;   // <-- callback

    public Receiver(int port)
    {
        this.port = port;
    }

    public void Start()
    {
        running = true;
        listenerThread = new Thread(ListenLoop);
        listenerThread.IsBackground = true;
        listenerThread.Start();
    }

    public void Stop()
    {
        running = false;
        listener?.Stop();
        listenerThread?.Abort();
    }

    private void ListenLoop()
    {
        listener = new TcpListener(IPAddress.Any, port);
        listener.Start();

        while (running)
        {
            if (!listener.Pending())
            {
                Thread.Sleep(10);
                continue;
            }

            TcpClient client = listener.AcceptTcpClient();
            NetworkStream stream = client.GetStream();
            byte[] buffer = new byte[2048];
            int bytesRead;

            while (running && (bytesRead = stream.Read(buffer, 0, buffer.Length)) != 0)
            {
                string msg = Encoding.UTF8.GetString(buffer, 0, bytesRead);

                //✓ Notify Unity-side logic
                OnMessageReceived?.Invoke(msg);
            }

            client.Close();
        }
    }

    public void Send(NetworkStream stream, string message)
    {
        byte[] bytes = Encoding.UTF8.GetBytes(message);
        stream.Write(bytes, 0, bytes.Length);
    }
}
