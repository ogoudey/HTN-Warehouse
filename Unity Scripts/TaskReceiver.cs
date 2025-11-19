using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEngine;

public class ReceiverBehaviour : MonoBehaviour
{
    [SerializeField] private int port = 5000;

    private Receiver receiver;
    private readonly object messageLock = new object();
    private Queue<Dictionary<string, string>> parsedMessages = new Queue<Dictionary<string, string>>();

    void Start()
    {
        receiver = new Receiver(port);

        receiver.OnMessageReceived += HandleMessageReceived;
        receiver.Start();

        Debug.Log($"Receiver started on port {port}");
    }

    void OnDestroy()
    {
        if (receiver != null)
        {
            receiver.Stop();
        }
    }

    /// <summary>
    /// Runs in background thread (from your Receiver)
    /// </summary>
    private void HandleMessageReceived(string msg)
    {
        var dict = ParseMessage(msg);

        lock (messageLock)
        {
            parsedMessages.Enqueue(dict);
        }
    }

    void Update()
    {
        // Pull parsed messages into Unity thread
        lock (messageLock)
        {
            while (parsedMessages.Count > 0)
            {
                var dict = parsedMessages.Dequeue();
                OnParsedMessage(dict);
            }
        }
    }

    /// <summary>
    /// Called on Unity main thread with parsed dictionary.
    /// </summary>
    private void OnParsedMessage(Dictionary<string, string> dict)
    {
        foreach (var kvp in dict)
        {
            Debug.Log($"[{kvp.Key}] = {kvp.Value}");
        }
    }

    /// <summary>
    /// Converts "[Robot: C, Container #2432: D, ...]" into a dictionary.
    /// </summary>
    public static Dictionary<string, string> ParseMessage(string msg)
    {
        Dictionary<string, string> result = new Dictionary<string, string>();

        // Remove brackets if present
        msg = msg.Trim().TrimStart('[').TrimEnd(']');

        // Split on ","
        string[] pairs = msg.Split(',');

        foreach (var p in pairs)
        {
            string pair = p.Trim();

            // Expect "Key: Value"
            int colonIndex = pair.IndexOf(':');
            if (colonIndex < 0) continue;

            string key = pair.Substring(0, colonIndex).Trim();
            string value = pair.Substring(colonIndex + 1).Trim();

            // Normalize key (remove spaces in "Container #2432")
            key = key.Replace(" ", "");

            if (!result.ContainsKey(key))
                result.Add(key, value);
        }

        return result;
    }
}
