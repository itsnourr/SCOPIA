package com.forensic.discovery;

import jakarta.annotation.PostConstruct;
import org.springframework.stereotype.Component;

import java.net.DatagramPacket;
import java.net.DatagramSocket;
import java.net.InetAddress;

@Component
public class UdpDiscoveryListener {

    private static final int DISCOVERY_PORT = 50000;
    private static final String DISCOVERY_MESSAGE = "DISCOVER_BACKEND";

    @PostConstruct
    public void startListener() {
        Thread listenerThread = new Thread(this::listen);
        listenerThread.setDaemon(true); // background thread
        listenerThread.start();
    }

    private void listen() {
        try (DatagramSocket socket = new DatagramSocket(DISCOVERY_PORT)) {
            System.out.println("UDP Discovery listener started on port " + DISCOVERY_PORT);

            byte[] buffer = new byte[1024];
            while (true) {
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                socket.receive(packet);
                String received = new String(packet.getData(), 0, packet.getLength());

                if (DISCOVERY_MESSAGE.equals(received)) {
                    // Send reply back with IP and port info
                    InetAddress clientAddress = packet.getAddress();
                    int clientPort = packet.getPort();
                    String reply = "BACKEND_IP:" + InetAddress.getLocalHost().getHostAddress() + ":8080";
                    DatagramPacket response = new DatagramPacket(
                            reply.getBytes(),
                            reply.length(),
                            clientAddress,
                            clientPort
                    );
                    socket.send(response);
                    System.out.println("Replied to discovery request from " + clientAddress);
                }
            }
        } catch (Exception e) {
            e.printStackTrace();
        }
    }
}